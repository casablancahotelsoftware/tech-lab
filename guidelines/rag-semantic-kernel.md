# Basic RAG application using Semantic Kernel

## Load the Documents
[Load-Documents](https://python.langchain.com/docs/how_to/document_loader_directory/)

## Create Vector Store Connectors
[Overview-of-the-Vector-Store](https://learn.microsoft.com/en-us/semantic-kernel/concepts/vector-store-connectors/?pivots=programming-language-csharp) Vector store connectors enable interaction with vector databases, storing embeddings for efficient retrieval. Here's how you can integrate one:

1. Install Qdrant Vector-Db locally: [Installation](https://qdrant.tech/documentation/guides/installation/)

2. Create a Collection: Use Semantic Kernel’s API to store embeddings. [Create-Collection](https://learn.microsoft.com/en-us/semantic-kernel/concepts/vector-store-connectors/?pivots=programming-language-csharp)

## How to Search for Relevant Content? 
- [How-to-Search](https://learn.microsoft.com/en-us/semantic-kernel/concepts/plugins/using-data-retrieval-functions-for-rag)
- [Text-Search-Vector-Stores](https://learn.microsoft.com/en-us/semantic-kernel/concepts/text-search/text-search-vector-stores?pivots=programming-language-csharp)

## Chat with RAG
Show-Case: https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/RAG/WithPlugins.cs

ChatModel Example: [ChatModel](https://learn.microsoft.com/en-us/semantic-kernel/concepts/ai-services/chat-completion/?tabs=csharp-AzureOpenAI%2Cpython-AzureOpenAI%2Cjava-AzureOpenAI&pivots=programming-language-csharp)

Chathistory Example: [ChatHistory](https://learn.microsoft.com/en-us/semantic-kernel/concepts/ai-services/chat-completion/chat-history?pivots=programming-language-csharp)

Another simple way to just use a StringBuilder to construct the context and then use it in a prompt:
```csharp

    using Microsoft.SemanticKernel;

    IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
    kernelBuilder.AddAzureOpenAIChatCompletion(
        deploymentName: "NAME_OF_YOUR_DEPLOYMENT",
        apiKey: "YOUR_API_KEY",
        endpoint: "YOUR_AZURE_ENDPOINT",
        modelId: "gpt-4", // Optional name of the underlying model if the deployment name doesn't match the model name
        serviceId: "YOUR_SERVICE_ID", // Optional; for targeting specific services within Semantic Kernel
        httpClient: new HttpClient() // Optional; if not provided, the HttpClient from the kernel will be used
    );
    Kernel kernel = kernelBuilder.Build();

    // Query the vector store to retrieve relevant documents
    var userQuery = "What are the key features of Semantic Kernel?";
    var retrievedDocuments = await vectorStore.SearchAsync(userQuery, maxResults: 5);

    // Placeholder embedding generation method.
    async Task<ReadOnlyMemory<float>> GenerateEmbeddingAsync(string textToVectorize)
    {
        // your logic here
    }

    // Create a Qdrant VectorStore object and choose an existing collection that already contains records.
    VectorStore vectorStore = new QdrantVectorStore(new QdrantClient("localhost"), ownsClient: true);
    VectorStoreCollection<ulong, Hotel> collection = vectorStore.GetCollection<ulong, Hotel>("skhotels");

    // Generate a vector for your search text, using your chosen embedding generation implementation.
    ReadOnlyMemory<float> searchVector = await GenerateEmbeddingAsync("I'm looking for a hotel where customer happiness is the priority.");

    // Do the search, passing an options object with a Top value to limit results to the single top match.
    var searchResult = collection.SearchAsync(searchVector, top: 1);


    var contextBuilder = new StringBuilder();
    contextBuilder.AppendLine("## Retrieved Knowledge Base Context");
    
    int documentIndex = 0;
    await foreach (var record in searchResult)
    {
        contextBuilder.AppendLine($"--- Document {documentIndex++} ---");
        contextBuilder.AppendLine($"Source: {record.Record.Url}");
        contextBuilder.AppendLine(record.Record.Description);
        contextBuilder.AppendLine();
    }

    contextBuilder.AppendLine("## User Query");
    contextBuilder.AppendLine(userQuery);


```
