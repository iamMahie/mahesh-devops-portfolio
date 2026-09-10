#-----------------------------------------------------------------------------------
# Stage 1: Build stage
#-----------------------------------------------------------------------------------
# Define the base image
FROM python:3.12-slim@sha256:2c941e860699f878900b0edc2403613c234d4b32eda3cc9fa7036991a2a63c4a AS base

# Set isolated environment for the application
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Mount the requirements.txt file and wheelhouse binaries to the build stage and install dependencies
# Mount cache for pip to speed up the build process for subsequent builds 
RUN --mount=type=bind,source=wed-studiozs/requirements.txt,target=/requirements.txt \
    --mount=type=bind,source=wed-studiozs/wheelhouse,target=/wh \
    --mount=type=cache,target=/root/.cache/pip \
    pip install --no-index --find-links=/wh -r /requirements.txt

# Stage the exact runtime subtree here; these layers are discarded with the build
# stage, so the runtime image pays for only one COPY.
COPY wed-studiozs/app        /stage/app
COPY wed-studiozs/alembic    /stage/alembic
COPY wed-studiozs/alembic.ini /stage/alembic.ini
# -----------------------------------------------------------------------------------
# Stage 2: Runtime stage
# -----------------------------------------------------------------------------------
# Define the base image for the runtime stage
FROM python:3.12-slim@sha256:2c941e860699f878900b0edc2403613c234d4b32eda3cc9fa7036991a2a63c4a AS runtime

# Set the working directory
WORKDIR /myapp

# Create the non-root user BEFORE copying, so we can set ownership in one step
# Install curl to use in the health check, and clean up apt cache to reduce image size
RUN addgroup --system fastapi \
    && adduser --system -u 999 --ingroup fastapi --no-create-home fastapiuser

# Get the islated environment from the build stage
COPY --from=base /opt/venv /opt/venv

# Set the PATH envrironment variable to use the isolated environment
ENV PATH="/opt/venv/bin:$PATH"

# Copy only the application subtree, so `app/` sits directly in WORKDIR
COPY --from=base --chown=fastapiuser:fastapi /stage/ ./

# Switch to the non-root user
USER fastapiuser

# Add a health check to ensure the application is running
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/readyz', timeout=4).status == 200 else 1)"]

# Expose the port fast api runs on
EXPOSE 8000

# Start the FastAPI application using uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]