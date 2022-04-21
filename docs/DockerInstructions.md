Copyright © `2022` `Kratos Technology & Training Solutions, Inc.`
Licensed under the MIT License.
SPDX-License-Identifier: MIT

Instructions for saving a docker image
  These instructions intend to prepare any Docker image for deployment within OpenSpace. They also serve to package up any docker image for delivery to another party.

See Also:
  https://docs.docker.com/engine/reference/commandline/save/

Context
  Docker images are akin to an entire OS image; they contain an OS, as well as all of the packages and scripts required for an application. As such, this is an increasingly popular way to version control an entire application. However, that also means that the files can be very large. See #TODO for file compression tricks.

  This instruction set assumes that the reader has a Dockerfile and a working knowledge of the Docker system.

Instructions
  1. cd to the directory that contains your Dockerfile.
  2. Build your docker image using the same 'docker build' command that your application requires
      _It is recommended that you use best practices for cleaning your environment and building the image from scratch_
  3. Find the IMAGE ID of your image with the 'docker images' command. It will be used below as <image_id>
  4. Issue this command to save the image as a gzip:
``      docker save <image_id> | gzip > filename.tar.gz``
  Your image is now saved and compressed, but likely a very large file (> 1 GB). Below are a few ideas to help you compress the image further.
  * Replace gzip with bzip2. Like this: 
``    docker save <image_id> | bzip2 > filename.tar.bz2``
  * Combine any consecutive RUN commands in your Dockerfile. Like this:
      Before:
``          RUN pip install --upgrade pip``
``          RUN pip install flask``
      After:
``          RUN pip install --upgrade pip; \``
``              pip install flask``