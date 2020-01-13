..  qs-static-site:

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
                namespace: static-site-dev
                # Disable CloudFront for development
                staticsite_cf_disable: true
              prod:
                namespace: static-site-prod
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
      [2020-01-13T11:59:42] STATIC WEBSITE URL: http://static-site-dev-site-bucket-45y5g8772n2r.s3-website-us-east-1.amazonaws.com
      [2020-01-13T11:59:42] staticsite: sync complete

Production Build
^^^^^^^^^^^^^^^^

#. You now have a static site deployed, however, we're not using best practices for a production type deployment. Let's add webpack and tell Runway to automatically build and deploy our production assets. First, let's switch to the `ENV-prod` branch to have Runway automatically detect our environment.

   .. code-block:: shell

    git co -b ENV-prod

#. In the `site` directory we're going to initialize a package.json file to include our javascript dependencies. Select all the default options unless you wish to change them.

   .. code-block:: shell

    cd site
    npm init

#. Open the generated file and update the `main` parameter to point to our scripts file at `assets/js/scripts.js`.

   .. code-block:: shell

    vi package.json

   .. code-block:: json

    {
      "name": "mystaticsite",
      "version": "1.0.0",
      "description": "",
      "main": "assets/js/scripts.js",
      "scripts": {
        "test": "echo \"Error: no test specified\" && exit 1"
      },
      "author": "",
      "license": "ISC"
    }

#. Save the file and exit. Next we're going to install webpack.

   .. code-block: shell

   npm install --save-dev webpack
