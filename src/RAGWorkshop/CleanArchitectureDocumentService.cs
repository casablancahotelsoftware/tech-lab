using Microsoft.Extensions.Logging;
using Microsoft.Extensions.VectorData;
using System.Text.Json;
using RAGWorkshop.Abstraction;
using RAGWorkshop.Model;

/// <summary>
/// Service for loading and processing CleanArchitecture documents for vector storage.
/// </summary>

public class CleanArchitectureDocumentService
{
    private readonly IEmbeddingService _embeddingService;
    private readonly ILogger<CleanArchitectureDocumentService> _logger;

    public CleanArchitectureDocumentService(
        IEmbeddingService embeddingService,
        ILogger<CleanArchitectureDocumentService> logger)
    {
        _embeddingService = embeddingService ?? throw new ArgumentNullException(nameof(embeddingService));
        _logger = logger ?? throw new ArgumentNullException(nameof(logger));
    }

    /// <summary>
    /// Load documents from JSON file created by the Python loader.
    /// </summary>
    public async Task<List<CleanArchitectureDocument>> LoadDocumentsFromJsonAsync(string filePath)
    {
        if (!File.Exists(filePath))
        {
            throw new FileNotFoundException($"Document file not found: {filePath}");
        }

        var documents = new List<CleanArchitectureDocument>();
        var jsonContent = await File.ReadAllTextAsync(filePath);

        try
        {
            var jsonArray = JsonSerializer.Deserialize<JsonElement[]>(jsonContent);

            foreach (var item in jsonArray)
            {
                var document = CleanArchitectureDocument.FromJson(item.GetRawText());
                documents.Add(document);
            }

            _logger.LogInformation("Loaded {DocumentCount} documents from {FilePath}", documents.Count, filePath);
            return documents;
        }
        catch (JsonException ex)
        {
            _logger.LogError(ex, "Failed to parse JSON from {FilePath}", filePath);
            throw;
        }
    }

    /// <summary>
    /// Load documents from JSONL file created by the Python loader.
    /// </summary>
    public async Task<List<CleanArchitectureDocument>> LoadDocumentsFromJsonLAsync(string filePath)
    {
        if (!File.Exists(filePath))
        {
            throw new FileNotFoundException($"Document file not found: {filePath}");
        }

        var documents = new List<CleanArchitectureDocument>();
        var lines = await File.ReadAllLinesAsync(filePath);

        foreach (var line in lines)
        {
            if (string.IsNullOrWhiteSpace(line)) continue;

            try
            {
                var document = CleanArchitectureDocument.FromJson(line);
                documents.Add(document);
            }
            catch (JsonException ex)
            {
                _logger.LogWarning(ex, "Failed to parse line: {Line}", line);
            }
        }

        _logger.LogInformation("Loaded {DocumentCount} documents from {FilePath}", documents.Count, filePath);
        return documents;
    }

    /// <summary>
    /// Generate embeddings for documents using the configured embedding service.
    /// </summary>
    public async Task GenerateEmbeddingsAsync(IEnumerable<CleanArchitectureDocument> documents,
        CancellationToken cancellationToken = default)
    {
        var documentList = documents.ToList();
        _logger.LogInformation("Generating embeddings for {DocumentCount} documents", documentList.Count);

        var batchSize = 10; // Process in batches to avoid overwhelming the embedding service
        var batches = documentList.Chunk(batchSize);

        foreach (var batch in batches)
        {
            var tasks = batch.Select(async document =>
            {
                try
                {
                    var embedding = await _embeddingService.GenerateEmbeddingAsync(document.Content);
                    document.ContentEmbedding = embedding;
                    _logger.LogDebug("Generated embedding for document {DocumentId}", document.Id);
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Failed to generate embedding for document {DocumentId}", document.Id);
                }
            });

            await Task.WhenAll(tasks);

            // Add a small delay between batches to be respectful to the embedding service
            await Task.Delay(100, cancellationToken);
        }

        var embeddedCount = documentList.Count(d => d.ContentEmbedding.HasValue);
        _logger.LogInformation("Successfully generated embeddings for {EmbeddedCount}/{TotalCount} documents",
            embeddedCount, documentList.Count);
    }

    /// <summary>
    /// Store documents in a vector store collection.
    /// </summary>
    public async Task StoreDocumentsAsync<TKey>(
        VectorStoreCollection<TKey, CleanArchitectureDocument> collection,
        IEnumerable<CleanArchitectureDocument> documents,
        CancellationToken cancellationToken = default)
        where TKey : notnull
    {
        var documentList = documents.ToList();
        _logger.LogInformation("Storing {DocumentCount} documents in vector store", documentList.Count);

        // Ensure collection exists
        var collectionExists = await collection.CollectionExistsAsync(cancellationToken);
        if (!collectionExists)
        {
            await collection.EnsureCollectionExistsAsync(cancellationToken);
            _logger.LogInformation("Created new collection");
        }

        // Store documents in batches
        var batchSize = 100;
        var batches = documentList.Chunk(batchSize);

        foreach (var batch in batches)
        {
            try
            {
                await collection.UpsertAsync(batch, cancellationToken);
                _logger.LogDebug("Stored batch of {BatchSize} documents", batch.Length);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to store batch of documents");
                throw;
            }
        }

        _logger.LogInformation("Successfully stored {DocumentCount} documents", documentList.Count);
    }

    /// <summary>
    /// Search for documents similar to a query.
    /// </summary>
    public async Task<List<VectorSearchResult<CleanArchitectureDocument>>> SearchDocumentsAsync<TKey>(
        VectorStoreCollection<TKey, CleanArchitectureDocument> collection,
        string query,
        VectorSearchOptions<CleanArchitectureDocument>? options = null,
        CancellationToken cancellationToken = default)
        where TKey : notnull
    {
        _logger.LogInformation("Searching for documents with query: {Query}", query);

        // Generate embedding for the query
        var queryEmbedding = await _embeddingService.GenerateEmbeddingAsync(query);

        // Search the collection
        var searchResults = new List<VectorSearchResult<CleanArchitectureDocument>>();
        await foreach (var result in collection.SearchAsync(queryEmbedding, top: 10, options, cancellationToken))
        {
            searchResults.Add(result);
        }

        _logger.LogInformation("Found {ResultCount} documents for query", searchResults.Count);
        return searchResults;
    }
}


