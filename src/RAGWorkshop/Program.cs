using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Qdrant;
using Qdrant.Client;
using RAGWorkshop.Services;
using Azure.AI.Inference;
using RAGWorkshop.Abstraction;
using Azure;
using RAGWorkshop.Model;

/// <summary>
/// Example program demonstrating how to use the CleanArchitecture document loader
/// with Semantic Kernel vector stores for to ingest documents and generate embeddings. 
/// </summary>
public class Program
{
    public static async Task Main(string[] args)
    {
        // Build configuration
        var configuration = new ConfigurationBuilder()
            .AddJsonFile("appsettings.json", optional: true)
            .Build();

        // Setup dependency injection
        var services = new ServiceCollection();
        ConfigureServices(services, configuration);
        
        var serviceProvider = services.BuildServiceProvider();
        var logger = serviceProvider.GetRequiredService<ILogger<Program>>();

        try
        {
            await RunExampleAsync(serviceProvider, logger);
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "An error occurred during execution");
        }
    }

    private static void ConfigureServices(IServiceCollection services, IConfiguration configuration)
    {
        // Configuration
        services.AddLogging();
        services.AddSingleton(configuration);

        var azureOpenAiEndpoint = configuration["AzureOpenAIEmbedding:Endpoint"]
            ?? throw new InvalidOperationException("Azure OpenAI endpoint not found in configuration");
        var azureOpenAiApiKey = configuration["AzureOpenAIEmbedding:ApiKey"]
            ?? throw new InvalidOperationException("OpenAI API key not found in configuration");

        var azureOpenAiEmbeddingModelId = configuration["OpenAI:EmbeddingModel"] ?? "text-embedding-3-large";

        // Changed to IEmbeddingGenerator
        services.AddSingleton<IEmbeddingService>(sp =>
            new AzureOpenAIEmbeddingService(
                new EmbeddingsClient(endpoint: new Uri(azureOpenAiEndpoint), credential: new AzureKeyCredential(azureOpenAiApiKey))));

        // Vector Store (Qdrant)
        var qdrantEndpoint = configuration["Qdrant:Endpoint"] ?? "http://localhost:6333";
        services.AddSingleton<VectorStore>(sp =>
            new QdrantVectorStore(
                new QdrantClient("localhost", port:6334),
                ownsClient: true));

        // Document processing service
        services.AddScoped<CleanArchitectureDocumentService>();
    }

    private static async Task RunExampleAsync(IServiceProvider serviceProvider, ILogger<Program> logger)
    {
        try
        {
            logger.LogInformation("Starting CleanArchitecture RAG Workshop Example");

            var documentService = serviceProvider.GetRequiredService<CleanArchitectureDocumentService>();
            var vectorStore = serviceProvider.GetRequiredService<VectorStore>();

            // Step 1: Load documents from JSON file (created by Python loader)
            var documentsFilePath = "./../../../../preprocessing/clean_architecture_documents.json";
        
            if (!File.Exists(documentsFilePath))
            {
                logger.LogWarning("Documents file not found: {FilePath}", documentsFilePath);
                logger.LogInformation("Please run the Python loader first to generate the documents file:");
                logger.LogInformation("python clean_architecture_loader.py");
                return;
            }

            var documents = await documentService.LoadDocumentsFromJsonAsync(documentsFilePath);
            logger.LogInformation("Loaded {DocumentCount} documents", documents.Count);
            Console.WriteLine($"Loaded {documents.Count} documents from {documentsFilePath}");

            // Step 3: Generate embeddings

            Console.WriteLine("Storing documents in vector database...");
            // Step 4: Store in vector database
            var collection = vectorStore.GetCollection<Guid, CleanArchitectureDocument>("cleanarchitecture");
            await collection.EnsureCollectionExistsAsync();

            Console.WriteLine("Generating embeddings for documents...");
            await documentService.GenerateEmbeddingsAsync(documents);
            Console.WriteLine("Embeddings generated successfully.");
            await documentService.StoreDocumentsAsync(collection, documents);
            Console.WriteLine("Documents stored successfully in vector database.");

        }
        catch (Exception ex)
        {
            Console.WriteLine(ex.Message);
            Console.WriteLine(ex.StackTrace);
            Console.WriteLine(ex.InnerException);
            return;
        }
       

        

    }
}
