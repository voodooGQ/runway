..  qs-staticsite:

Static Site Quickstart
======================

Prerequisites
^^^^^^^^^^^^^

- An AWS account, and configured terminal environment for interacting with it via an admin role.
- The following installed tools:

  - npm
  - git (Available out of the box on macOS)
  - vi (or a text editor of your choosing)


#. Download/install Runway. Here we are showing the :ref:`curl<install-curl>`
   option. To see other available install methods, see
   :ref:`Installation<install>`.

   .. rubric:: macOS

   .. code-block:: shell

       curl -L https://oni.ca/latest/osx/runway -o runway
       chmod +x runway

   .. rubric:: Ubuntu

   .. code-block:: shell

       curl -L https://oni.ca/latest/ubnt/runway -o runway
       chmod +x runway

   .. rubric:: Windows

   .. code-block:: shell

       curl -L https://oni.ca/latest/win/runway -o runway

Site Setup
^^^^^^^^^^

#. Prepare the base project directory. See :ref:`Repo Structure<repo-structure>`
   for more details.

   .. code-block:: shell

       mkdir mystaticsite
       cd mystaticsite
       git init
       git checkout -b ENV-dev

#. Create the main source directory for the site.

   .. code-block:: shell

       mkdir site
       cd site

#. Create the asset directories and return to the site source directory.

   .. code-block:: shell

       mkdir assets
       cd assets
       mkdir js
       mkdir css
       cd ..

#. Create the main `index.html` document.

   .. code-block:: shell

     touch index.html
     vi index.html

   .. code-block:: html

      <html lang="en">
        <head>
          <meta charset="utf-8">

          <title>My Static Site</title>
          <meta name="description" content="My Static Site deployed via Runway">
          <meta name="author" content="Your Name Here">

          <link rel="stylesheet" href="assets/css/styles.css?v=1.0">

        </head>

        <body>
          <main id="main"></main>
          <script src="assets/js/scripts.js"></script>
        </body>
      </html>

#. Let's make some minor css changes to have a dark background with light text.

   .. code-block:: shell

     cd assets/css
     touch styles.css
     vi styles.css

   .. code-block:: css

    html, body {
      background: #222;
      color: #ffffff;
    }

#. Now let's create our main "Hello World" script.

   .. code-block:: shell

     cd ../js
     touch scripts.js
     vi scripts.js

   .. code-block:: js

     document.getElementById("main").innerHTML = "<div>Hello World!</div>"

Runway Setup
^^^^^^^^^^^^

#. Our basic site is ready to go! If you open the `index.html` document in a browser you should see the message "Hello World!" displayed. Time to setup our runway document for deployment. From the current `js` directory:

   .. code-block:: shell

     cd ../../../
     touch runway.yml
     vi runway.yml

   .. code-block:: yaml

      deployments:
        - modules:
          - path: site
            class_path: runway.module.staticsite.StaticSite
            environments:
              dev:
                namespace: staticsite-dev
                # Disable CloudFront for development
                staticsite_cf_disable: true
              prod:
                namespace: staticsite-prod
          regions:
            - us-east-1

Deploy
^^^^^^

#. Our initial deployment is ready to go. In our case we're going to be deploying to the `dev` environment which disables CloudFront. CloudFront is a CDN and considered best practice when deploying static sites, however, it takes a significant amount of time to allocate and will slow down our development cycle. From the root directory issue the following command to deploy our `dev` environment configuration.


   .. code-block:: shell

    runway deploy

#. After a few minutes, so long as everything was successful, you should be presented with an output of the static sites website URL. Below is an example.

   .. code-block:: shell

      # ect...
      [2020-01-13T11:59:42] Shutdown request received in result processing thread, shutting down result thread.
      [2020-01-13T11:59:42] STATIC WEBSITE URL: http://staticsite-dev-site-bucket-45y5g8772n2r.s3-website-us-east-1.amazonaws.com
      [2020-01-13T11:59:42] staticsite: sync complete

Production Build
^^^^^^^^^^^^^^^^

#. You now have a static site deployed, however, we're not using best practices for a production type deployment. Let's add webpack and tell Runway to automatically build and deploy our production assets. First, let's switch to the `ENV-prod` branch to have Runway automatically detect our environment.

   .. code-block:: shell

    git co -b ENV-prod

#. In the `site` directory we're first going to remove our stylesheet and script tags from the `index.html` document and then move it into the `assets` folder. This keeps everything tidy for webpack.

   .. code-block:: shell

    vi index.html

   .. code-block:: html

      <html lang="en">
        <head>
          <meta charset="utf-8">

          <title>My Static Site</title>
          <meta name="description" content="My Static Site deployed via Runway">
          <meta name="author" content="Your Name Here">
        </head>

        <body>
          <main id="main"></main>
        </body>
      </html>

   .. code-block:: shell

     mv index.html assets/

#. Now we need to create a package.json file to retrieve our dependencies.

   .. code-block:: shell

    touch package.json
    vi package.json

   .. code-block:: json

    {
      "name": "mystaticsite",
      "version": "1.0.0",
      "description": "My awesome static site!",
      "main": "./assets/js/scripts.js",
      "scripts": {
        "build": "webpack --config webpack.config.js"
      },
      "devDependencies": {
        "@babel/cli": "^7.7.4",
        "@babel/core": "^7.7.4",
        "@babel/preset-env": "^7.7.4",
        "babel-loader": "^8.0.6",
        "css-loader": "^3.2.1",
        "cssnano": "^4.1.0",
        "glob": "^7.1.6",
        "html-webpack-plugin": "^3.0.0",
        "mini-css-extract-plugin": "^0.8.0",
        "optimize-css-assets-webpack-plugin": "^5.0.3",
        "raw-loader": "^3.1.0",
        "webpack": "^4.41.2",
        "webpack-cli": "^3.1.0",
        "webpack-dev-server": "^3.9.0",
        "webpack-merge": "^4.2.2"
      }
    }

#. Next we need to create our webpack configuration file.

   .. code-block:: shell

    touch webpack.config.json
    vi webpack.config.json

   .. code-block:: js

    const glob = require('glob');
    const path = require('path');
    const cssnano = require('cssnano');

    const HTMLWebpackPlugin = require('html-webpack-plugin');
    const MiniCssExtractPlugin = require('mini-css-extract-plugin');
    const OptimizeCssAssetsPlugin = require('optimize-css-assets-webpack-plugin');

    const generateHTMLPlugins = () => glob.sync('./assets/**/*.html').map(
      dir => new HTMLWebpackPlugin({
        filename: path.basename(dir), // Output
        template: dir, // Input
      }),
    );

    module.exports = {
      node: {
        fs: 'empty',
      },
      entry: ['./assets/js/scripts.js', './assets/css/styles.css'],
      mode: 'production',
      output: {
        path: path.resolve(__dirname, 'dist'),
        filename: 'app.bundle.js',
      },
      module: {
        rules: [
          {
            test: /\.js$/,
            loader: 'babel-loader',
          },
          {
            test: /\.html$/,
            loader: 'raw-loader',
          },
          {
            test: /\.css$/,
            use: [
              { loader: MiniCssExtractPlugin.loader },
              'css-loader',
            ],
          }
        ],
      },
      plugins: [
        new MiniCssExtractPlugin({
          filename: '[name].css',
          chunkFilename: '[id].css',
        }),
        new OptimizeCssAssetsPlugin({
          assetNameRegExp: /\.css$/g,
          cssProcessor: cssnano,
          cssProcessorOptions: { discardComments: { removeAll: true } },
          canPrint: true,
        }),
        ...generateHTMLPlugins() ],
      stats: {
        colors: true,
      },
      devtool: 'source-map',
    };

#. Let's head back to our `runway.yml` file and tell runway to build the created production package upon deploy. The updated `runway.yml` file should look like the following.

   .. code-block:: shell

      cd ..
      vi runway.yml

   .. code-block:: yaml

    deployments:
      - modules:
        - path: site
          class_path: runway.module.staticsite.StaticSite
          environments:
            dev:
              namespace: static-site-dev
              staticsite_cf_disable: true
            prod:
              namespace: static-site-prod
          options:
            # The output directory from webpack
            build_output: dist
            # The steps to build our site
            build_steps:
              - npm install
              - npm run build
        regions:
          - us-east-1

#. Finally you can deploy your new production optimized environment by running `runway deploy` from your root directory.

Destroy
^^^^^^^

#. Destroying our site is just as easy as creating it! If you followed the tutorial up to this point you'll be on the
`ENV-prod` branch of your repository, from here we can destroy the production build with the following.

   .. code-block:: shell

    runway destroy

#. To destroy our development build we simply need to switch branches to `ENV-dev` and run the destroy command.

   .. code-block:: shell

    git co ENV-dev
    runway destroy


Conclusion
^^^^^^^^^^

This example demonstrates a rudimentary static site build with an production build steps. If you want to get off the ground and running quicker Runway comes standard with sample generation for a React or Angular static site with the respective commands `runway gen-sample static-react` or `runway gen-sample static-angular`
