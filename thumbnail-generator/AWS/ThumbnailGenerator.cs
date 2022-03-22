using System.IO;
using System.Threading.Tasks;
using Amazon.Lambda.Core;
using Amazon.XRay.Recorder.Core;
using Amazon.XRay.Recorder.Handlers.AwsSdk;
using Amazon.Lambda.APIGatewayEvents;
using Amazon.S3;
using Amazon.S3.Model;
using Amazon.Lambda.S3Events;

[assembly: LambdaSerializer(typeof(Amazon.Lambda.Serialization.Json.JsonSerializer))]

namespace ThumbnailGenerator.AWS
{
  public class Upload
  {
    static Upload() {
      AWSSDKHandler.RegisterXRayForAllServices();
    }

    public async Task<APIGatewayProxyResponse> Handler(APIGatewayProxyRequest apiRequest)
    {
        AWSXRayRecorder.Instance.BeginSubsegment("Upload Preparation");
        var imageName = apiRequest.QueryStringParameters["filename"];
        var bucketName = System.Environment.GetEnvironmentVariable("IMAGE_BUCKET");
        byte[] data = System.Convert.FromBase64String(apiRequest.Body);
        var stream = new MemoryStream(data);
        AWSXRayRecorder.Instance.EndSubsegment();

        AWSXRayRecorder.Instance.BeginSubsegment("Upload S3 PUT Operation");
        var s3Client = new AmazonS3Client();
        var request = new PutObjectRequest
        {
            BucketName = bucketName,
            InputStream = stream,
            ContentType = "image/jpg",
            Key = $"input/{imageName}"
        };
        await s3Client.PutObjectAsync(request).ConfigureAwait(false);
        AWSXRayRecorder.Instance.EndSubsegment();

        return new APIGatewayProxyResponse
        {
            StatusCode = 200,
        };
    }

  }

  public class CreateThumbnail
  {
    static CreateThumbnail() {
      AWSSDKHandler.RegisterXRayForAllServices();
    }

    public async Task<string> Handler(S3Event s3Event)
    {
      AWSXRayRecorder.Instance.BeginSubsegment("CreateThumbnail Read Operation");

      var record = s3Event.Records[0];
      var s3 = record.S3;

      // Read image
      var _s3Client = new AmazonS3Client();
      GetObjectRequest getObjectRequest = new GetObjectRequest
      {
          BucketName = s3.Bucket.Name,
          Key = s3.Object.Key
      };
      var getObjectResponse = await _s3Client.GetObjectAsync(getObjectRequest);

      AWSXRayRecorder.Instance.EndSubsegment();

      // Resize it
      var _imageHelper = new ImageHelper();
      var imageSmall = _imageHelper.ResizeImage(getObjectResponse.ResponseStream);

      AWSXRayRecorder.Instance.BeginSubsegment("CreateThumbnail S3 PUT Operation");

      // Upload image 
      var _s3Client2 = new AmazonS3Client();
      var request = new PutObjectRequest
      {
          BucketName = s3.Bucket.Name,
          InputStream = imageSmall,
          ContentType = "image/jpg",
          Key = s3.Object.Key.Replace("input/", "output/")
      };
      await _s3Client2.PutObjectAsync(request);

      AWSXRayRecorder.Instance.EndSubsegment();
      
      return "OK";  
    }

  }
}