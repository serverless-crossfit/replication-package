using System;
using System.IO;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Azure.WebJobs;
using Microsoft.Azure.WebJobs.Extensions.Http;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Logging;
using System.Collections.Generic;
using Microsoft.ApplicationInsights.DataContracts;
using Microsoft.ApplicationInsights;
using Microsoft.ApplicationInsights.Extensibility;
using System.Diagnostics;
using Microsoft.Azure.EventGrid.Models;
using Microsoft.Azure.WebJobs.Extensions.EventGrid;
using Newtonsoft.Json.Linq;

namespace ThumbnailGenerator.Azure
{
    public class ThumbnailGenerator
    {
        private readonly TelemetryClient _telemetryClient;

        public ThumbnailGenerator(TelemetryConfiguration telemetryConfiguration)
        {
            _telemetryClient = new TelemetryClient(telemetryConfiguration);
        }
    
        [FunctionName("Upload")]
        [StorageAccount("AzureWebJobsStorage")]
        public async Task<IActionResult> Upload(
            [HttpTrigger(AuthorizationLevel.Anonymous, "get", "post", Route = "upload/{name}")] HttpRequest req,
            string name,
            ILogger log,
            ExecutionContext context)
        {       
            DateTime start = DateTime.UtcNow;

            // Decode and read image data into Stream
            string requestBody = await new StreamReader(req.Body).ReadToEndAsync();
            byte[] data = System.Convert.FromBase64String(requestBody);
            var imageStream = new MemoryStream(data);

            if (req.Headers.TryGetValue("traceparent", out var traceparent))
            {
                _telemetryClient.TrackTrace("Upload Blob Operation Starts",
                        SeverityLevel.Information,
                        new Dictionary<string,string> { {"TraceId", traceparent[0].Split("-")[1]} });
            }  

            // Upload image to Azure Blob Storage
            var _blobHelper = new BlobHelper();
            var blob = _blobHelper.GetCloudBlockBlob(context, "input", name);
            await blob.UploadFromStreamAsync(imageStream); 
        
            var requestTelemetry = req.HttpContext?.Features.Get<RequestTelemetry>();

            // Set Metadata of blob to include tracing information
            blob.Metadata.Add("TraceId", traceparent[0].Split("-")[1]);
            blob.Metadata.Add("ParentId", requestTelemetry.Id);
            await blob.SetMetadataAsync();

            // Log a custom dependency in the dependencies table.
            var dependency = new DependencyTelemetry
            {
                Name = "Upload function execution",
                Timestamp = start,
                Duration = DateTime.UtcNow - start,
                Success = true
            };

            dependency.Context.Operation.Id = traceparent[0].Split("-")[1];
            dependency.Context.Operation.ParentId = requestTelemetry.Id;

            _telemetryClient.TrackDependency(dependency);

            return new OkObjectResult(name + "Uploaded successfully.");
        }  

        [FunctionName("Create-Thumbnail")]
        public async Task CreateThumbnail([EventGridTrigger]EventGridEvent e, ILogger log, ExecutionContext context)
        {   
            DateTime start = DateTime.UtcNow; 
            
            // Reference: https://github.com/paolosalvatori/blob-event-grid-function-app/blob/master/README.md
            var blobCreatedEvent = ((JObject)e.Data).ToObject<StorageBlobCreatedEventData>();
            var name = blobCreatedEvent.Url.Split('/')[blobCreatedEvent.Url.Split('/').Length - 1];

            // Read image
            var _blobHelper = new BlobHelper();
            var inputBlob = _blobHelper.GetCloudBlockBlob(context, "input", name);
            var imageStream = await inputBlob.OpenReadAsync();

            // Resize image
            var _imageHelper = new ImageHelper();
            var imageSmall = _imageHelper.ResizeImage(imageStream);
            // Empty file issue: https://stackoverflow.com/questions/48592752/uploading-to-azure-storage-returning-an-empty-file
            imageSmall.Position = 0;
           
            if(inputBlob.Metadata.TryGetValue("TraceId", out string traceId))
            {
                // Correlate with previous function
                Activity.Current?.AddTag("TraceId",traceId);
                Activity.Current?.AddBaggage("TraceId", traceId);

                _telemetryClient.TrackTrace("CreateThumbnail PUT Operation Starts",
                        SeverityLevel.Information,
                        new Dictionary<string,string> { {"TraceId", traceId} });
            }  

            // Upload image
            var blob = _blobHelper.GetCloudBlockBlob(context, "output", name);
            await blob.UploadFromStreamAsync(imageSmall);
            
            // Log a custom dependency in the dependencies table.
            var dependency = new DependencyTelemetry
            {
                Name = "CreateThumbnail execution",
                Timestamp = start,
                Duration = DateTime.UtcNow - start,
                Success = true
            };

            if(inputBlob.Metadata.TryGetValue("ParentId", out string parentId))
            {
                dependency.Context.Operation.Id = traceId;
                dependency.Context.Operation.ParentId = parentId;
            }

            _telemetryClient.TrackDependency(dependency);
        }
    }
}
