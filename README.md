# Thalia Backend - Setup Guide

This guide will help you set up and run the Thalia Backend application, which is a Django-based server for generating stories with audio.

## Prerequisites

- Python 3.8+ installed
- Git (optional, for cloning the repository)
- An available port (default: 8000)

## Installation Steps

### 1. Clone or Download the Repository

```bash
git clone <repository-url>
cd ThaliaBackend
```

### 2. Create a Virtual Environment

```bash
# On Windows
python -m venv .venv
.venv\Scripts\activate

# On macOS/Linux
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the root directory based on the `.env.default` template:

```bash
# Copy the default environment file
cp .env.default .env
```

Edit the `.env` file with your actual settings:

- `LLM_CONTAINER_URL`: URL to your LLM service
- Email settings for password reset functionality:
  - `EMAIL_HOST`: SMTP server (default: smtp.gmail.com)
  - `EMAIL_PORT`: SMTP port (default: 587)
  - `EMAIL_HOST_USER`: Your email address
  - `EMAIL_HOST_PASSWORD`: Your email app password
  - `DEFAULT_FROM_EMAIL`: Sender email address

### 5. Set Up the Database

```bash
python manage.py migrate
```

### 6. Create a Superuser (Optional)

```bash
python manage.py createsuperuser
```

## Running the Application

### Start the Development Server

```bash
python manage.py runserver 0.0.0.0:8000
```

The application will be available at:

- Local access: <http://127.0.0.1:8000>
- Network access: <http://your-ip-address:8000>

## API Endpoints

The application exposes several API endpoints under `/api/`:

- Authentication:
  - `/api/signup/` - Create a new user account
  - `/api/login/` - Log in with email and password
  - `/api/logout/` - Log out (requires authentication)

- User Management:
  - `/api/change-password/` - Change user password
  - `/api/change-email/` - Change user email
  - `/api/request-password-reset/` - Request a password reset
  - `/api/confirm-password-reset/` - Confirm password reset with token

- Story Operations:
  - `/api/create-story/` - Create a new story
  - `/api/stories/` - Get all stories for the authenticated user
  - `/api/story/<story_id>/` - Get details for a specific story
  - `/api/like-story/` - Like a story
  - `/api/unlike-story/` - Unlike a story

## WebSocket Support

The application also supports WebSocket connections for real-time updates:

- `/ws/jobs/<user_id>/` - Connect to receive updates for story generation jobs

## Additional Information

- Admin interface: Available at `/admin/` after creating a superuser
- The application uses Django Channels for WebSocket support
- Story generation is handled asynchronously through a job queue

Happy storytelling with Thalia!
