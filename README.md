# FPF Backend

## Overview

FPF is a backend API built with FastAPI. It provides various endpoints for authentication, data management, and more.

## Getting Started

### Prerequisites

- Python 3.8+
- PostgreSQL
- FastAPI
- Alembic

### Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/your-repo/FPF.git
    cd FPF
    ```

2. Create and activate a virtual environment:
    ```sh
    python -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    ```

3. Install the dependencies:
    ```sh
    pip install -r requirements.txt
    ```

4. Set up the environment variables:
    Create a [.env](http://_vscodecontentref_/6) file in the root directory with the following content:
    ```env
    # App Name
    APP_NAME=FPF

    # FastAPI
    SECRET_KEY=<>uuid.uuid4().hex<>

    # Database
    POSTGRESQL_DATABASE=postgresql+asyncpg://my_user:my_password@host-name/db-name

    # SMTP
    SMTP_SERVER=smtp.gmail.com
    SMTP_PORT=587
    EMAIL_ADDRESS=""
    EMAIL_PASSWORD=""
    ```

5. Run the database migrations:
    ```sh
    alembic upgrade head
    ```

### Running the Project

To run the project, use the following command:
```sh
fastapi dev
```

### API Documentation
    Once the server is running, you can access the API documentation at:

    - Swagger UI
    - ReDoc

### License
    This project is licensed under the MIT License. See the LICENSE file for details.

```
This `README.md` provides a clear structure, links to relevant files, and instructions for setting up and running the project.
```