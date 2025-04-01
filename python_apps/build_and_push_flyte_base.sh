docker build --pull --rm -f "Dockerfile.flyte_worker_base" -t flyte_base:latest .
docker image tag flyte_base:latest api-xp.iopex.ai/flyte_base:latest
docker image push api-xp.iopex.ai/flyte_base:latest