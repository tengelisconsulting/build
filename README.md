# Overview
This is a simple build server, which listens for github webhooks and runs build commands defined as executables in a /build directory at the root of the
relevant repository.  The hooks presently defined, in order, as: "pre_build", "build", "test", "push" and "post_push".

This is essentially the same as how autobuilds are defined on DockerHub with respect to github pushes.
I happily used Dockerhub for some time this way, but was motivated to run my own build server after experiencing sporadic and unexplainable errors
with the DockerHub infrastructure.

The server currently runs one build at a time, in a background thread.
To allow synchronous builds the build execution would need to be performed on isolated network stacks in order to prevent port collision during testing,
among other issues.
In the future I would like to investigate dynamically provisioning build execution environments on demand,
perhaps up to some maximum number of parallel builds.


# Requirements
## Packages
System: docker, git, python3.8

Python: see [requirements.txt](https://github.com/tengelisconsulting/build/blob/master/requirements.txt)

# Setup
- Install the above packages on a dedicated server
- Configure a github webhook on the repository you want to build for to send a JSON-encoded POST request to <your_server_host>:<your-port>/on-push
- Clone the repo
- Create an env file using env.sample as a template.  See [env.sample](https://github.com/tengelisconsulting/build/blob/master/env.sample)
- Source the env file, run main.py
- Builds should now be kicked off on each push to github
