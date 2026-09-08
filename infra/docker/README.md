# infra/docker

Owner: person 1

Shared Dockerfiles / compose overrides that don't belong inside a single service folder
(e.g. an nginx reverse-proxy config, shared base images). Individual services keep their
own `Dockerfile` inside their own folder.
