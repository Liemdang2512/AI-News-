# Project Overview

This is a full-stack news aggregator web application that uses AI to summarize and categorize news articles from various Vietnamese newspapers.

**Key Technologies:**

*   **Backend:** Python with FastAPI is used for the backend. It handles fetching and parsing RSS feeds, filtering articles by date and time, and interacting with the Google Gemini API for summarization and categorization.
*   **Frontend:** The frontend is a modern web application built with Next.js, React, and Tailwind CSS. It provides a user-friendly interface for searching, viewing, and summarizing news articles.
*   **AI:** The application leverages the Google Gemini API for its AI-powered features, including article summarization and categorization.

**Architecture:**

The application follows a client-server architecture. The frontend is a single-page application (SPA) that communicates with the backend via a REST API. The backend is a stateless service that can be scaled independently of the frontend.

# Building and Running

## Backend

To run the backend, follow these steps:

1.  Navigate to the `backend` directory.
2.  Create a virtual environment: `python3 -m venv venv`
3.  Activate the virtual environment: `source venv/bin/activate`
4.  Install the required dependencies: `pip install -r requirements.txt`
5.  Create a `.env` file from the example: `cp .env.example .env`
6.  Add your Google Gemini API key to the `.env` file.
7.  Start the backend server: `uvicorn main:app --reload --host 0.0.0.0 --port 8000`

## Frontend

To run the frontend, follow these steps:

1.  Navigate to the `frontend` directory.
2.  Install the required dependencies: `npm install`
3.  Create a `.env.local` file from the example: `cp .env.local.example .env.local`
4.  Start the frontend development server: `npm run dev`

# Development Conventions

*   **Coding Style:** The project uses the default coding styles for Python and TypeScript.
*   **Testing:** There are no tests in the project.
*   **Contributing:** There are no contribution guidelines in the project.
