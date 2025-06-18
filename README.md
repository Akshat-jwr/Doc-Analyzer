# AI-Powered Document Intelligence Platform

A powerful and intuitive platform that enables users to interact with their documents through natural language conversations, leverage AI for deep insights, perform intelligent modifications of structured data, and visualize extracted information. This application is designed to enhance document comprehension, analysis, and collaboration by bridging the gap between raw data and actionable intelligence.

## ✨ Features

*   **Multi-Document Analysis**: Upload and analyze multiple PDF documents, extracting diverse content types for comprehensive insights.
*   **Intelligent AI Chat Interface**: Engage in natural language conversations with your documents. The AI provides insights, summaries, answers to queries, and context-aware explanations based on document content.
*   **Document Preview & Interaction**: Offers a real-time preview of uploaded documents, allowing users to navigate content and interact directly, potentially highlighting sections for focused AI analysis.
*   **Advanced Content Extraction**: Utilizes sophisticated processing to extract `TextChunk` (raw text), `Table` (structured tabular data), and `Image` (visual elements) from documents, forming the foundation for AI analysis.
*   **AI-Driven Table Modification**: Request the AI to modify tables within documents based on natural language commands. The system generates structured output including a modification summary, a clean modified table, and a detailed change log.
*   **High-Performance Table Rendering**: Efficiently displays even very large tables using frontend virtualization techniques, ensuring smooth scrolling and optimal performance without impacting browser responsiveness.
*   **Data Export & Download**: Download modified tables directly from the chat interface as Excel files for further analysis or as Markdown files for easy sharing.
*   **Interactive Visualizations**: Provides capabilities for generating and displaying visual representations of extracted data and information retrieval results, with a focus on user-specific insights.
*   **Conversation Management**: Manage chat histories, with potential features for saving, clearing, and forking conversations to explore different discussion paths.
*   **Responsive & Intuitive UI**: Features a clean, modern, and responsive user interface designed for a seamless and engaging user experience.
*   **Robust File Handling**: Leverages Cloudinary for secure and efficient storage and delivery of all document assets.

## 🛠️ Technology Stack

This platform is built with a modern and robust technology stack, ensuring scalability, performance, and maintainability.

*   **Frontend**:
    *   **Next.js**: React-based framework for server-side rendering, routing, and efficient frontend development.
    *   **React**: JavaScript library for building user interfaces.
    *   **TypeScript**: Strongly-typed superset of JavaScript for enhanced code quality and maintainability.
    *   **Tailwind CSS**: Utility-first CSS framework for rapid and consistent UI styling.
    *   **Zustand**: Fast and lightweight state management solution for React applications.
    *   **Axios**: Promise-based HTTP client for making API requests.
    *   **`react-window`**: Library for efficient virtualization of large lists and tabular data.
    *   **`react-markdown`**: React component to render Markdown as React components.
    *   **`remark-gfm`**: `remark` plugin to support GitHub Flavored Markdown (GFM), essential for table rendering.
*   **Backend**:
    *   **Python**: Primary programming language for backend services.
    *   **FastAPI**: Modern, fast (high-performance) web framework for building APIs with Python 3.7+ based on standard Python type hints.
    *   **LangChain**: Framework for developing applications powered by large language models.
    *   **Beanie**: Asynchronous MongoDB ODM for Python, simplifying database interactions.
    *   **MongoDB**: NoSQL database for flexible and scalable data storage.
*   **AI/LLM**:
    *   Integrated with various Large Language Models (LLMs) (e.g., OpenAI, Groq, Llama3, Mixtral, Gemma) for conversational AI and advanced analysis.
*   **Cloud Services**:
    *   **Cloudinary**: Cloud-based service for image and video management, used for storing and delivering document assets.

## 🏗️ Architecture Overview

The platform follows a clear separation of concerns, divided into frontend, backend, and a core document processing pipeline.

### Frontend Structure

*   **Next.js Application**: Serves as the web application framework, providing routing, API routes, and static asset serving.
*   **Component-Based UI**: Built with reusable React components (e.g., `Button`, `Layout`, `LoadingSpinner`) to ensure modularity and ease of development.
    *   **`MessageBubble`**: The core component for displaying chat messages. It intelligently renders different content types:
        *   Standard text and small tables using `ReactMarkdown` with `remark-gfm`.
        *   Large tables using a dedicated `VirtualizedTable` component for performance.
        *   Displays rich metadata like download buttons for modified tables.
    *   **`VirtualizedTable`**: A specialized component utilizing `react-window` to render large tabular data efficiently, ensuring smooth scrolling.
    *   **`DocumentToolbar`**: Handles interactive elements related to document viewing (e.g., zoom controls).
*   **State Management**: Utilizes `useChatStore` (Zustand) for global state management related to chat sessions, messages, and application-wide settings.
*   **API Client**: An `api.ts` utility (Axios-based) centralizes all frontend-to-backend communication.
*   **Styling**: Consistent and responsive styling achieved with Tailwind CSS.

### Backend Services

*   **FastAPI Application**: The core API layer that handles all incoming requests and routes them to appropriate services.
*   **`MultiChatService`**: The central service for all chat-related functionalities:
    *   Manages `ChatSession` and `ChatMessage` lifecycles.
    *   Integrates with LLMs for generating conversational responses and performing advanced analytical tasks.
    *   Handles **AI-driven table modifications**, parsing complex LLM outputs into structured data (summary, change log, modified table Markdown).
    *   Manages chat history and context for LLM interactions.
*   **`ContentExtractorService` (Conceptual)**: Responsible for the initial processing of uploaded documents:
    *   Parses document content into structured data models: `TextChunk`, `Table`, and `Image`.
    *   These extracted components are stored in MongoDB and serve as the analytical basis for the chat service.
*   **Database Models**: Uses Beanie to define models for `User`, `Document`, `TextChunk`, `Table`, `Image`, `ChatSession`, and `ChatMessage`, persisted in MongoDB.
*   **Authentication**: Secure user authentication handled via standard API practices.
*   **File Storage Integration**: Interacts with Cloudinary for robust storage and delivery of all document assets.
*   **Download Service**: An `EnhancedTableDownloadService` (or similar logic) in the API layer facilitates the export of modified tables into formats like Excel or Markdown.

### Document Processing Workflow

1.  **Upload**: Users upload documents (e.g., PDFs).
2.  **Extraction**: The `ContentExtractorService` processes the document, extracting:
    *   **Text Chunks**: Paragraphs, sentences, or other raw text units.
    *   **Tables**: Structured data identified within the document.
    *   **Images**: Visual elements detected.
3.  **Storage**: Extracted data is stored in MongoDB, linked to the original `Document` record.
4.  **Analysis**: This structured data (`TextChunk`, `Table`, `Image`) becomes the input for the `MultiChatService` and other analytical functions. Chat sessions can be initiated for a document as long as the document exists, regardless of the presence of specific content types.

## 🚀 Getting Started

To get a local copy up and running, follow these simple steps.

### Prerequisites

*   Node.js (LTS version recommended)
*   Python 3.9+
*   MongoDB instance (local or cloud-hosted)
*   Cloudinary Account (with API Key, API Secret, Cloud Name)
*   LLM Provider Account (e.g., OpenAI, Groq)

### Installation

1.  **Clone the repository**:
    ```
    git clone [your-repository-url]
    cd [your-repository-name]
    ```

2.  **Backend Setup**:
    ```
    cd backend # or the directory containing your FastAPI app
    pip install -r requirements.txt
    ```
    Create a `.env` file in your backend root directory and configure environment variables (replace placeholders with your actual credentials):
    ```
    MONGO_URI="mongodb://localhost:27017/your_db_name"
    CLOUD_NAME="your_cloudinary_cloud_name"
    API_KEY="your_cloudinary_api_key"
    API_SECRET="your_cloudinary_api_secret"
    LLM_API_KEY="your_llm_api_key"
    # Add any other environment variables as required by your specific LLM or services
    ```

3.  **Frontend Setup**:
    ```
    cd frontend # or the directory containing your Next.js app
    npm install # or yarn install
    ```
    Create a `.env.local` file in your frontend root directory:
    ```
    NEXT_PUBLIC_BACKEND_URL="http://localhost:8000" # Or your backend's URL
    ```

### Running the Application

1.  **Start the Backend**:
    ```
    cd backend
    uvicorn main:app --reload
    ```
    (Adjust `main:app` if your FastAPI app is named differently)

2.  **Start the Frontend**:
    ```
    cd frontend
    npm run dev # or yarn dev
    ```

The application should now be accessible in your browser, typically at `http://localhost:3000`.

## 💡 Usage

1.  **Upload Documents**: Navigate to the document management section to upload your PDF files.
2.  **Start a Chat**: Select a document and choose to start either a "General Chat" or an "Analytical Chat" based on your needs.
3.  **Interact with AI**: Type your questions or commands in natural language.
4.  **Modify Tables**: Ask the AI to make specific changes to tables, like "change the CGPA for 2027 to 10".
5.  **Download Results**: If a table is modified, a download button will appear, allowing you to export the modified table as an Excel file.

## 🤝 Contributing

We welcome contributions! If you'd like to improve this project, please follow these steps:

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/your-feature-name`).
3.  Make your changes.
4.  Commit your changes (`git commit -m 'Add new feature'`).
5.  Push to the branch (`git push origin feature/your-feature-name`).
6.  Open a Pull Request.

## 📄 License

This project is licensed under the [Your Chosen License, e.g., MIT License]. See the `LICENSE` file for details.
