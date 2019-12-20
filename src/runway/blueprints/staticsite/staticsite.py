#!/usr/bin/env python
"""Module with static website bucket and CloudFront distribution."""
from __future__ import print_function

import hashlib
# https://github.com/PyCQA/pylint/issues/73
from distutils.version import LooseVersion  # noqa pylint: disable=no-name-in-module,import-error
from past.builtins import basestring

import awacs.s3
import awacs.sts
from awacs.aws import Allow, PolicyDocument, Principal, Statement

from stacker.blueprints.base import Blueprint
from stacker.blueprints.variables.types import CFNCommaDelimitedList, CFNString
from stacker.context import Context

import troposphere
from troposphere import (
    AWSProperty, And, Equals, If, Join, Not, NoValue, Output, Select,
    awslambda, cloudfront, iam, s3
)

IAM_ARN_PREFIX = 'arn:aws:iam::aws:policy/service-role/'
if LooseVersion(troposphere.__version__) == LooseVersion('2.4.0'):
    from troposphere.validators import boolean, priceclass_type

    class S3OriginConfig(AWSProperty):
        """Backported s3 origin config class for broken troposphere release."""

        props = {
            'OriginAccessIdentity': (basestring, False),
        }

    class Origin(AWSProperty):
        """Backported origin config class for broken troposphere release."""

        props = {
            'CustomOriginConfig': (cloudfront.CustomOriginConfig, False),
            'DomainName': (basestring, True),
            'Id': (basestring, True),
            'OriginCustomHeaders': ([cloudfront.OriginCustomHeader], False),
            'OriginPath': (basestring, False),
            'S3OriginConfig': (S3OriginConfig, False),
        }

    class DistributionConfig(AWSProperty):
        """Backported cf config class for broken troposphere release."""

        props = {
            'Aliases': (list, False),
            'CacheBehaviors': ([cloudfront.CacheBehavior], False),
            'Comment': (basestring, False),
            'CustomErrorResponses': ([cloudfront.CustomErrorResponse], False),
            'DefaultCacheBehavior': (cloudfront.DefaultCacheBehavior, True),
            'DefaultRootObject': (basestring, False),
            'Enabled': (boolean, True),
            'HttpVersion': (basestring, False),
            'IPV6Enabled': (boolean, False),
            'Logging': (cloudfront.Logging, False),
            'Origins': ([Origin], True),
            'PriceClass': (priceclass_type, False),
            'Restrictions': (cloudfront.Restrictions, False),
            'ViewerCertificate': (cloudfront.ViewerCertificate, False),
            'WebACLId': (basestring, False),
        }


class StaticSite(Blueprint):  # pylint: disable=too-few-public-methods
    """Stacker blueprint for creating S3 bucket and CloudFront distribution."""

    VARIABLES = {
        'AcmCertificateArn': {'type': CFNString,
                              'default': '',
                              'description': '(Optional) Cert ARN for site'},
        'Aliases': {'type': CFNCommaDelimitedList,
                    'default': '',
                    'description': '(Optional) Domain aliases the '
                                   'distribution'},
        'LogBucketName': {'type': CFNString,
                          'default': '',
                          'description': 'S3 bucket for CF logs'},
        'PriceClass': {'type': CFNString,
                       'default': 'PriceClass_100',  # US/Europe
                       'description': 'CF price class for the distribution.'},
        'RewriteDirectoryIndex': {'type': CFNString,
                                  'default': '',
                                  'description': '(Optional) File name to '
                                                 'append to directory '
                                                 'requests.'},
        'WAFWebACL': {'type': CFNString,
                      'default': '',
                      'description': '(Optional) WAF id to associate with the '
                                     'distribution.'},
        'custom_error_responses': {'type': list,
                                   'default': [],
                                   'description': '(Optional) Custom error '
                                                  'responses.'},
        'lambda_function_associations': {'type': list,
                                         'default': [],
                                         'description': '(Optional) Lambda '
                                                        'function '
                                                        'associations.'},
        }

    def add_oai_resource(self, template):
        return template.add_resource(
            cloudfront.CloudFrontOriginAccessIdentity(
                'OAI',
                CloudFrontOriginAccessIdentityConfig=cloudfront.CloudFrontOriginAccessIdentityConfig(  # noqa pylint: disable=line-too-long
                    Comment='CF access to website'
                )
            )
        )

    def add_website_bucket_resource(self, template):
        return template.add_resource(
            s3.Bucket(
                'Bucket',
                AccessControl=s3.Private,
                LifecycleConfiguration=s3.LifecycleConfiguration(
                    Rules=[
                        s3.LifecycleRule(
                            NoncurrentVersionExpirationInDays=90,
                            Status='Enabled'
                        )
                    ]
                ),
                VersioningConfiguration=s3.VersioningConfiguration(
                    Status='Enabled'
                ),
                WebsiteConfiguration=s3.WebsiteConfiguration(
                    IndexDocument='index.html',
                    ErrorDocument='error.html'
                )
            )
        )

    def add_cloudfront_access_policy_resource(self, template, oai, bucket):
        return template.add_resource(
            s3.BucketPolicy(
                'AllowCFAccess',
                Bucket=bucket.ref(),
                PolicyDocument=PolicyDocument(
                    Version='2012-10-17',
                    Statement=[
                        Statement(
                            Action=[awacs.s3.GetObject],
                            Effect=Allow,
                            Principal=Principal(
                                'CanonicalUser',
                                oai.get_att('S3CanonicalUserId')
                            ),
                            Resource=[
                                Join('', [bucket.get_att('Arn'),
                                          '/*'])
                            ]
                        )
                    ]
                )
            )
        )

    def add_cloudfront_directory_index_rewrite_role(self, template):
        return template.add_resource(
            iam.Role(
                'CFDirectoryIndexRewriteRole',
                Condition='DirectoryIndexSpecified',
                AssumeRolePolicyDocument=PolicyDocument(
                    Version='2012-10-17',
                    Statement=[
                        Statement(
                            Effect=Allow,
                            Action=[awacs.sts.AssumeRole],
                            Principal=Principal('Service',
                                                ['lambda.amazonaws.com',
                                                 'edgelambda.amazonaws.com'])
                        )
                    ]
                ),
                ManagedPolicyArns=[
                    IAM_ARN_PREFIX + 'AWSLambdaBasicExecutionRole'
                ]
            )
        )

    def add_cloudfront_directory_index_rewrite_lambda_resource(self, template, index_rewrite_role):
        variables = self.get_variables()

        return template.add_resource(
            awslambda.Function(
                'CFDirectoryIndexRewrite',
                Condition='DirectoryIndexSpecified',
                Code=awslambda.Code(
                    ZipFile=Join(
                        '',
                        ["'use strict';\n",
                         "exports.handler = async function(event, context) {\n",
                         "\n",
                         "    // Extract the request from the CloudFront event that is sent to Lambda@Edge\n",  # noqa pylint: disable=line-too-long
                         "    var request = event.Records[0].cf.request;\n",
                         "    // Extract the URI from the request\n",
                         "    var olduri = request.uri;\n",
                         "    // Match any '/' that occurs at the end of a URI. Replace it with a default index\n",  # noqa pylint: disable=line-too-long
                         "    var newuri = olduri.replace(/\\/$/, '\\/",
                         variables['RewriteDirectoryIndex'].ref,
                         "');\n",  # noqa
                         "    // Log the URI as received by CloudFront and the new URI to be used to fetch from origin\n",  # noqa pylint: disable=line-too-long
                         "    console.log(\"Old URI: \" + olduri);\n",
                         "    console.log(\"New URI: \" + newuri);\n",
                         "    // Replace the received URI with the URI that includes the index page\n",  # noqa pylint: disable=line-too-long
                         "    request.uri = newuri;\n",
                         "    // Return to CloudFront\n",
                         "    return request;\n",
                         "\n",
                         "};\n"]
                    )
                ),
                Description='Rewrites CF directory HTTP requests to default page',  # noqa
                Handler='index.handler',
                Role=index_rewrite_role.get_att('Arn'),
                Runtime='nodejs10.x'
            )
        )

    def add_cloudfront_directory_index_rewrite_lambda_version_resource(
            self,
            template,
            rewrite_lambda,
            code_hash
    ):
        return template.add_resource(
            awslambda.Version(
                'CFDirectoryIndexRewriteVer' + code_hash,
                Condition='DirectoryIndexSpecified',
                FunctionName=rewrite_lambda.ref()
            )
        )

    def add_lambda_associations(self, lambda_version):
        variables = self.get_variables()

        # If custom associations defined, use them
        if variables['lambda_function_associations']:
            return [
                cloudfront.LambdaFunctionAssociation(
                    EventType=x['type'],
                    LambdaFunctionARN=x['arn']
                ) for x in variables['lambda_function_associations']
            ]

        return If(
            'DirectoryIndexSpecified',
            [cloudfront.LambdaFunctionAssociation(
                EventType='origin-request',
                LambdaFunctionARN=lambda_version.ref()
            )],
            NoValue
        )

    def add_cloudfront_distribution_resource(
            self,
            template,
            oai,
            bucket,
            lambda_function_associations,
            access_policy
    ):
        variables = self.get_variables()

        cf_dist_opts = {
            'Aliases': If(
                'AliasesSpecified',
                variables['Aliases'].ref,
                NoValue
            ),
            'Origins': [
                get_cf_origin_class()(
                    DomainName=Join(
                        '.',
                        [bucket.ref(),
                         's3.amazonaws.com']),
                    S3OriginConfig=get_s3_origin_conf_class()(
                        OriginAccessIdentity=Join(
                            '',
                            ['origin-access-identity/cloudfront/',
                             oai.ref()])
                    ),
                    Id='S3Origin'
                )
            ],
            'DefaultCacheBehavior': cloudfront.DefaultCacheBehavior(
                AllowedMethods=['GET', 'HEAD'],
                Compress=False,
                DefaultTTL='86400',
                ForwardedValues=cloudfront.ForwardedValues(
                    Cookies=cloudfront.Cookies(Forward='none'),
                    QueryString=False,
                ),
                LambdaFunctionAssociations=lambda_function_associations,
                TargetOriginId='S3Origin',
                ViewerProtocolPolicy='redirect-to-https'
            ),
            'DefaultRootObject': 'index.html',
            'Logging': If(
                'CFLoggingEnabled',
                cloudfront.Logging(
                    Bucket=Join('.',
                                [variables['LogBucketName'].ref,
                                 's3.amazonaws.com'])
                ),
                NoValue
            ),
            'PriceClass': variables['PriceClass'].ref,
            'Enabled': True,
            'WebACLId': If(
                'WAFNameSpecified',
                variables['WAFWebACL'].ref,
                NoValue
            ),
            'ViewerCertificate': If(
                'AcmCertSpecified',
                cloudfront.ViewerCertificate(
                    AcmCertificateArn=variables['AcmCertificateArn'].ref,
                    SslSupportMethod='sni-only'
                ),
                NoValue
            )
        }

        # If custom error responses defined, use them
        if variables['custom_error_responses']:
            cf_dist_opts['CustomErrorResponses'] = [
                cloudfront.CustomErrorResponse(
                    **x
                ) for x in variables['custom_error_responses']
            ]

        return template.add_resource(
            get_cf_distribution_class()(
                'CFDistribution',
                DependsOn=access_policy.title,
                DistributionConfig=get_cf_distro_conf_class()(
                    **cf_dist_opts
                )
            )
        )

    def add_bucket_name_output(self, template, bucket):
        return template.add_output(Output(
            'BucketName',
            Description='Name of website bucket',
            Value=bucket.ref()
        ))

    def add_cloudfront_distribution_id_output(self, template, cfdistribution):
        return template.add_output(Output(
            'CFDistributionId',
            Description='CloudFront distribution ID',
            Value=cfdistribution.ref()
        ))

    def add_cloudfront_distribution_domain_output(self, template, cfdistribution):
        return template.add_output(
            Output(
                'CFDistributionDomainName',
                Description='CloudFront distribution domain name',
                Value=cfdistribution.get_att('DomainName')
            )
        )

    def cloudfront_setup(self, template, bucket):
        oai = self.add_oai_resource(template)
        access_policy = self.add_cloudfront_access_policy_resource(template, oai, bucket)
        role = self.add_cloudfront_directory_index_rewrite_role(template)
        rewrite_lambda = self.add_cloudfront_directory_index_rewrite_lambda_resource(
            template, role
        )

        # Generating a unique resource name here for the Lambda version, so it
        # updates automatically if the lambda code changes
        code_hash = hashlib.md5(
            str(rewrite_lambda.properties['Code'].properties['ZipFile'].to_dict()).encode()  # noqa pylint: disable=line-too-long
        ).hexdigest()

        lambda_ver = self.add_cloudfront_directory_index_rewrite_lambda_version_resource(
            template,
            rewrite_lambda,
            code_hash,
        )

        lambda_function_associations = self.add_lambda_associations(lambda_ver)

        cfdistribution = self.add_cloudfront_distribution_resource(
            template,
            oai,
            bucket,
            lambda_function_associations,
            access_policy
        )

        self.add_cloudfront_distribution_id_output(template, cfdistribution)
        self.add_cloudfront_distribution_domain_output(template, cfdistribution)

    def website_bucket_setup(self, template):
        bucket = self.add_website_bucket_resource(template)
        self.add_bucket_name_output(template, bucket)
        return bucket

    def create_template(self):
        """Create template (main function called by Stacker)."""
        template = self.template
        variables = self.get_variables()
        template.set_version('2010-09-09')
        template.set_description('Static Website - Bucket and Distribution')

        # Conditions
        template.add_condition(
            'AcmCertSpecified',
            And(Not(Equals(variables['AcmCertificateArn'].ref, '')),
                Not(Equals(variables['AcmCertificateArn'].ref, 'undefined')))
        )
        template.add_condition(
            'AliasesSpecified',
            And(Not(Equals(Select(0, variables['Aliases'].ref), '')),
                Not(Equals(Select(0, variables['Aliases'].ref), 'undefined')))
        )
        template.add_condition(
            'CFLoggingEnabled',
            And(Not(Equals(variables['LogBucketName'].ref, '')),
                Not(Equals(variables['LogBucketName'].ref, 'undefined')))
        )
        template.add_condition(
            'DirectoryIndexSpecified',
            And(Not(Equals(variables['RewriteDirectoryIndex'].ref, '')),
                Not(Equals(variables['RewriteDirectoryIndex'].ref, 'undefined')))  # noqa
        )
        template.add_condition(
            'WAFNameSpecified',
            And(Not(Equals(variables['WAFWebACL'].ref, '')),
                Not(Equals(variables['WAFWebACL'].ref, 'undefined')))
        )

        # Resources
        bucket = self.website_bucket_setup(template)
        # self.cloudfront_setup(template, bucket)


def get_cf_distribution_class():
    """Return the correct troposphere CF distribution class."""
    if LooseVersion(troposphere.__version__) == LooseVersion('2.4.0'):
        cf_dist = cloudfront.Distribution
        cf_dist.props['DistributionConfig'] = (DistributionConfig, True)
        return cf_dist
    return cloudfront.Distribution


def get_cf_distro_conf_class():
    """Return the correct troposphere CF distribution class."""
    if LooseVersion(troposphere.__version__) == LooseVersion('2.4.0'):
        return DistributionConfig
    return cloudfront.DistributionConfig


def get_cf_origin_class():
    """Return the correct Origin class for troposphere."""
    if LooseVersion(troposphere.__version__) == LooseVersion('2.4.0'):
        return Origin
    return cloudfront.Origin


def get_s3_origin_conf_class():
    """Return the correct S3 Origin Config class for troposphere."""
    if LooseVersion(troposphere.__version__) > LooseVersion('2.4.0'):
        return cloudfront.S3OriginConfig
    if LooseVersion(troposphere.__version__) == LooseVersion('2.4.0'):
        return S3OriginConfig
    return cloudfront.S3Origin


# Helper section to enable easy blueprint -> template generation
# (just run `python <thisfile>` to output the json)
if __name__ == "__main__":
    print(StaticSite('test', Context({"namespace": "test"}), None).to_json())
