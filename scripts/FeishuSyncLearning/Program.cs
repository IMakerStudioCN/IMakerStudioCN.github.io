using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;

// 这个教学版与 scripts/sync-feishu-submissions.mjs 的职责相同：
//   sync：读取飞书中“已通过且未同步”的记录，写入 resources.json。
//   mark：PR 创建后，把 PR 地址回写到飞书的“同步状态”。
//
// 它不会自己创建 Git 分支或 PR。创建分支、PR 和执行合并属于
// GitHub Actions workflow 的“编排职责”，不属于这个程序的“业务职责”。

return await ProgramEntry.RunAsync(args);

internal static class ProgramEntry
{
    public static async Task<int> RunAsync(string[] args)
    {
        try
        {
            // args 是命令行参数。执行 `dotnet run -- sync` 时，args[0] 就是 sync。
            string mode = args.Length > 0 ? args[0].Trim().ToLowerInvariant() : "sync";

            // 配置只读取一次，然后通过构造函数交给服务对象。
            // 这比在各个方法中反复读取环境变量更容易测试和维护。
            AppConfig config = AppConfig.FromEnvironment();

            // using 会在程序结束时释放 HttpClient 占用的资源。
            // 对这种短生命周期的命令行程序，一个共享 HttpClient 就足够了。
            using var httpClient = new HttpClient
            {
                Timeout = TimeSpan.FromSeconds(30)
            };

            var feishu = new FeishuClient(httpClient, config);
            var synchronizer = new ResourceSynchronizer(config, feishu);

            switch (mode)
            {
                case "sync":
                    await synchronizer.SyncAsync();
                    break;

                case "mark":
                    await synchronizer.MarkSubmittedAsync();
                    break;

                default:
                    throw new ArgumentException($"未知模式：{mode}。只能使用 sync 或 mark。");
            }

            // 返回 0 代表程序成功。GitHub Actions 会据此把步骤标为成功。
            return 0;
        }
        catch (Exception exception)
        {
            // 把错误写到标准错误流，并返回非 0 退出码。
            // GitHub Actions 看到退出码 1 后会停止后续的默认步骤。
            Console.Error.WriteLine($"同步失败：{exception.Message}");
            Console.Error.WriteLine(exception.StackTrace);
            return 1;
        }
    }
}

internal sealed class AppConfig
{
    public required string AppId { get; init; }
    public required string AppSecret { get; init; }
    public required string AppToken { get; init; }
    public required string TableId { get; init; }
    public required string ViewId { get; init; }
    public required string ApprovedValue { get; init; }
    public required string SubmittedValue { get; init; }
    public required string SyncMode { get; init; }
    public required string RecordFile { get; init; }
    public required FieldNames Fields { get; init; }

    public static AppConfig FromEnvironment()
    {
        string syncMode = Optional("FEISHU_SYNC_MODE", "all").ToLowerInvariant();
        if (syncMode is not ("all" or "latest"))
        {
            throw new InvalidOperationException(
                $"FEISHU_SYNC_MODE 只能是 all 或 latest，当前值：{syncMode}");
        }

        return new AppConfig
        {
            // Secret 和必需标识没有默认值，缺失时应立即失败。
            AppId = Required("FEISHU_APP_ID"),
            AppSecret = Required("FEISHU_APP_SECRET"),
            AppToken = Required("FEISHU_APP_TOKEN"),
            TableId = Required("FEISHU_TABLE_ID"),

            // 可选配置提供默认值，使同一份代码能适配不同表格。
            ViewId = Optional("FEISHU_VIEW_ID", ""),
            ApprovedValue = Optional("FEISHU_APPROVED_VALUE", "已通过"),
            SubmittedValue = Optional("FEISHU_SUBMITTED_VALUE", "已提交审核"),
            SyncMode = syncMode,
            RecordFile = Optional("FEISHU_RECORD_FILE", ".feishu-sync-records.json"),
            Fields = new FieldNames
            {
                Name = Optional("FEISHU_FIELD_NAME", "资源名称"),
                Url = Optional("FEISHU_FIELD_URL", "资源链接"),
                Description = Optional("FEISHU_FIELD_DESCRIPTION", "资源简介"),
                Category = Optional("FEISHU_FIELD_CATEGORY", "内容分类"),
                Type = Optional("FEISHU_FIELD_TYPE", "资源类型"),
                Tags = Optional("FEISHU_FIELD_TAGS", "标签"),
                Cover = Optional("FEISHU_FIELD_COVER", "封面地址"),
                Review = Optional("FEISHU_FIELD_REVIEW", "审核状态"),
                Sync = Optional("FEISHU_FIELD_SYNC", "同步状态"),
                CreatedTime = Optional("FEISHU_FIELD_CREATED_TIME", "投稿时间")
            }
        };
    }

    private static string Required(string name)
    {
        string? value = Environment.GetEnvironmentVariable(name)?.Trim();
        if (string.IsNullOrWhiteSpace(value))
        {
            throw new InvalidOperationException($"缺少环境变量 {name}");
        }

        return value;
    }

    private static string Optional(string name, string defaultValue)
    {
        string? value = Environment.GetEnvironmentVariable(name)?.Trim();
        return string.IsNullOrWhiteSpace(value) ? defaultValue : value;
    }
}

internal sealed class FieldNames
{
    public required string Name { get; init; }
    public required string Url { get; init; }
    public required string Description { get; init; }
    public required string Category { get; init; }
    public required string Type { get; init; }
    public required string Tags { get; init; }
    public required string Cover { get; init; }
    public required string Review { get; init; }
    public required string Sync { get; init; }
    public required string CreatedTime { get; init; }
}

internal sealed class FeishuClient
{
    private const string ApiRoot = "https://open.feishu.cn/open-apis";
    private readonly HttpClient _httpClient;
    private readonly AppConfig _config;
    private string? _tenantToken;

    public FeishuClient(HttpClient httpClient, AppConfig config)
    {
        _httpClient = httpClient;
        _config = config;
    }

    public async Task<List<FeishuRecord>> ListRecordsAsync()
    {
        var records = new List<FeishuRecord>();
        string pageToken = "";

        // 飞书一次最多返回一页数据，所以必须循环读取，直到 has_more=false。
        do
        {
            var queryParts = new List<string>
            {
                "page_size=500",
                "with_automatic_fields=true"
            };

            if (!string.IsNullOrEmpty(_config.ViewId))
            {
                queryParts.Add($"view_id={Uri.EscapeDataString(_config.ViewId)}");
            }

            if (!string.IsNullOrEmpty(pageToken))
            {
                queryParts.Add($"page_token={Uri.EscapeDataString(pageToken)}");
            }

            string path =
                $"/bitable/v1/apps/{Uri.EscapeDataString(_config.AppToken)}" +
                $"/tables/{Uri.EscapeDataString(_config.TableId)}" +
                $"/records?{string.Join("&", queryParts)}";

            JsonElement data = await SendAsync(HttpMethod.Get, path, body: null);

            if (data.TryGetProperty("items", out JsonElement items) &&
                items.ValueKind == JsonValueKind.Array)
            {
                foreach (JsonElement item in items.EnumerateArray())
                {
                    records.Add(FeishuRecord.FromJson(item));
                }
            }

            bool hasMore = data.TryGetProperty("has_more", out JsonElement hasMoreElement) &&
                           hasMoreElement.ValueKind == JsonValueKind.True;

            pageToken = hasMore &&
                        data.TryGetProperty("page_token", out JsonElement tokenElement)
                ? tokenElement.GetString() ?? ""
                : "";
        }
        while (!string.IsNullOrEmpty(pageToken));

        return records;
    }

    public async Task UpdateSyncStatusAsync(string recordId, string value)
    {
        string path =
            $"/bitable/v1/apps/{Uri.EscapeDataString(_config.AppToken)}" +
            $"/tables/{Uri.EscapeDataString(_config.TableId)}" +
            $"/records/{Uri.EscapeDataString(recordId)}";

        // Dictionary 允许在运行时使用字段名。
        // 若配置中的同步字段叫“同步状态”，序列化结果就是：
        // { "fields": { "同步状态": "已提交审核：https://..." } }
        var body = new
        {
            fields = new Dictionary<string, string>
            {
                [_config.Fields.Sync] = value
            }
        };

        await SendAsync(HttpMethod.Put, path, body);
    }

    private async Task<string> GetTenantTokenAsync()
    {
        // 一次程序运行只申请一次 Token，后续请求复用它。
        if (!string.IsNullOrEmpty(_tenantToken))
        {
            return _tenantToken;
        }

        using HttpResponseMessage response = await _httpClient.PostAsJsonAsync(
            $"{ApiRoot}/auth/v3/tenant_access_token/internal/",
            new
            {
                app_id = _config.AppId,
                app_secret = _config.AppSecret
            });

        string responseText = await response.Content.ReadAsStringAsync();
        using JsonDocument document = JsonDocument.Parse(responseText);
        JsonElement root = document.RootElement;

        int code = root.TryGetProperty("code", out JsonElement codeElement)
            ? codeElement.GetInt32()
            : -1;

        if (!response.IsSuccessStatusCode || code != 0 ||
            !root.TryGetProperty("tenant_access_token", out JsonElement tokenElement))
        {
            string message = root.TryGetProperty("msg", out JsonElement messageElement)
                ? messageElement.GetString() ?? "未知错误"
                : $"HTTP {(int)response.StatusCode}";

            throw new HttpRequestException($"获取飞书访问凭证失败：{message}");
        }

        _tenantToken = tokenElement.GetString();
        if (string.IsNullOrEmpty(_tenantToken))
        {
            throw new HttpRequestException("飞书响应中没有 tenant_access_token");
        }

        return _tenantToken;
    }

    private async Task<JsonElement> SendAsync(HttpMethod method, string path, object? body)
    {
        string token = await GetTenantTokenAsync();

        using var request = new HttpRequestMessage(method, $"{ApiRoot}{path}");
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);

        if (body is not null)
        {
            string json = JsonSerializer.Serialize(body, JsonOptions.Default);
            request.Content = new StringContent(json, Encoding.UTF8, "application/json");
        }

        using HttpResponseMessage response = await _httpClient.SendAsync(request);
        string responseText = await response.Content.ReadAsStringAsync();
        using JsonDocument document = JsonDocument.Parse(responseText);
        JsonElement root = document.RootElement;

        int code = root.TryGetProperty("code", out JsonElement codeElement)
            ? codeElement.GetInt32()
            : -1;

        if (!response.IsSuccessStatusCode || code != 0)
        {
            string message = root.TryGetProperty("msg", out JsonElement messageElement)
                ? messageElement.GetString() ?? "未知错误"
                : $"HTTP {(int)response.StatusCode}";

            throw new HttpRequestException($"飞书接口失败：{message}");
        }

        // JsonDocument 离开 using 后会被释放，因此必须 Clone()，
        // 否则返回的 JsonElement 会引用已经释放的内存。
        return root.TryGetProperty("data", out JsonElement data)
            ? data.Clone()
            : JsonDocument.Parse("{}").RootElement.Clone();
    }
}

internal sealed class ResourceSynchronizer
{
    private readonly AppConfig _config;
    private readonly FeishuClient _feishu;

    public ResourceSynchronizer(AppConfig config, FeishuClient feishu)
    {
        _config = config;
        _feishu = feishu;
    }

    public async Task SyncAsync()
    {
        List<FeishuRecord> records = await _feishu.ListRecordsAsync();

        string sourceJson = await File.ReadAllTextAsync("resources.json");
        ResourceFile source = JsonSerializer.Deserialize<ResourceFile>(sourceJson, JsonOptions.Default)
            ?? throw new InvalidOperationException("resources.json 内容为空或格式不正确");

        // HashSet 的查找速度快，适合做去重。
        // Add() 在元素已存在时返回 false，因此还能发现同一批次中的重复 URL。
        var existingUrls = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (Resource resource in source.Resources)
        {
            string existingUrl = ValueConverter.NormalizeUrl(resource.Url) ?? resource.Url.Trim();
            existingUrls.Add(existingUrl);
        }

        List<FeishuRecord> eligibleRecords = records
            .OrderByDescending(record => record.GetCreatedTime(_config.Fields.CreatedTime))
            .Where(record =>
                record.GetText(_config.Fields.Review) == _config.ApprovedValue &&
                string.IsNullOrEmpty(record.GetText(_config.Fields.Sync)))
            .ToList();

        Console.WriteLine($"同步模式：{(_config.SyncMode == "latest" ? "仅处理最新一条" : "处理全部")}");
        Console.WriteLine($"待检查投稿：{eligibleRecords.Count} 条");

        var accepted = new List<AcceptedRecord>();
        var skipped = new List<string>();
        int processedCount = 0;

        foreach (FeishuRecord record in eligibleRecords)
        {
            processedCount++;

            Resource resource = ConvertToResource(record);
            List<string> errors = Validate(resource);

            if (errors.Count > 0)
            {
                skipped.Add($"{RecordLabel(record, resource.Name)}：{string.Join("、", errors)}");
                continue;
            }

            string? normalizedUrl = ValueConverter.NormalizeUrl(resource.Url);
            if (normalizedUrl is null)
            {
                skipped.Add($"{RecordLabel(record, resource.Name)}：链接格式错误");
                continue;
            }

            resource.Url = normalizedUrl;
            if (!existingUrls.Add(normalizedUrl))
            {
                skipped.Add($"{RecordLabel(record, resource.Name)}：链接已存在");
                continue;
            }

            source.Resources.Add(resource);
            accepted.Add(new AcceptedRecord
            {
                RecordId = record.RecordId,
                Name = resource.Name,
                Url = resource.Url
            });

            // latest 不是只看最新一条，而是找到最新的一条“有效记录”后停止。
            // 因此最新记录缺字段时，会继续检查下一条。
            if (_config.SyncMode == "latest")
            {
                break;
            }
        }

        if (_config.SyncMode == "latest" && processedCount < eligibleRecords.Count)
        {
            Console.WriteLine($"延后处理投稿：{eligibleRecords.Count - processedCount} 条");
        }

        foreach (string message in skipped)
        {
            Console.WriteLine($"跳过记录：{message}");
        }

        if (accepted.Count == 0)
        {
            await GitHubActionsOutput.WriteAsync("has_changes", "false");
            await GitHubActionsOutput.WriteAsync("count", "0");
            Console.WriteLine("没有待同步且审核通过的飞书记录。");
            return;
        }

        // resources.json 使用上海时区的日期，与现有项目保持一致。
        TimeZoneInfo shanghai = FindShanghaiTimeZone();
        DateTimeOffset localNow = TimeZoneInfo.ConvertTime(DateTimeOffset.UtcNow, shanghai);
        source.UpdatedAt = localNow.ToString("yyyy.MM.dd");

        string outputJson = JsonSerializer.Serialize(source, JsonOptions.Default);
        await File.WriteAllTextAsync("resources.json", outputJson + Environment.NewLine);

        // 这个临时文件充当 sync 和 mark 两个命令之间的数据交接物。
        // mark 不重新猜测哪些记录属于当前 PR，而是精确读取本次接受的记录 ID。
        string acceptedJson = JsonSerializer.Serialize(accepted, JsonOptions.Default);
        await File.WriteAllTextAsync(_config.RecordFile, acceptedJson + Environment.NewLine);

        // $GITHUB_OUTPUT 是 GitHub Actions 为当前 step 提供的特殊文件。
        // workflow 后续可以通过 steps.sync.outputs.has_changes 读取这些值。
        await GitHubActionsOutput.WriteAsync("has_changes", "true");
        await GitHubActionsOutput.WriteAsync("count", accepted.Count.ToString());
        await GitHubActionsOutput.WriteAsync("names", string.Join("、", accepted.Select(item => item.Name)));

        Console.WriteLine($"已写入 {accepted.Count} 条资源，等待创建 Pull Request。");
    }

    public async Task MarkSubmittedAsync()
    {
        string pullRequestUrl = Environment.GetEnvironmentVariable("PULL_REQUEST_URL")?.Trim()
            ?? "";

        if (string.IsNullOrEmpty(pullRequestUrl))
        {
            throw new InvalidOperationException("缺少环境变量 PULL_REQUEST_URL");
        }

        string recordJson = await File.ReadAllTextAsync(_config.RecordFile);
        List<AcceptedRecord> records =
            JsonSerializer.Deserialize<List<AcceptedRecord>>(recordJson, JsonOptions.Default)
            ?? throw new InvalidOperationException($"无法读取 {_config.RecordFile}");

        foreach (AcceptedRecord record in records)
        {
            string value = $"{_config.SubmittedValue}：{pullRequestUrl}";
            await _feishu.UpdateSyncStatusAsync(record.RecordId, value);
            Console.WriteLine($"已回写投稿：{record.Name}（飞书记录 ID：{record.RecordId}）");
        }

        Console.WriteLine($"已回写 {records.Count} 条飞书记录的同步状态。");
    }

    private Resource ConvertToResource(FeishuRecord record)
    {
        var resource = new Resource
        {
            Name = record.GetText(_config.Fields.Name),
            Description = record.GetText(_config.Fields.Description),
            Url = record.GetUrl(_config.Fields.Url),
            Category = record.GetText(_config.Fields.Category),
            Type = record.GetText(_config.Fields.Type),
            Tags = record.GetTags(_config.Fields.Tags)
        };

        string? cover = ValueConverter.NormalizeUrl(record.GetUrl(_config.Fields.Cover));
        if (cover is not null)
        {
            resource.Cover = cover;
        }

        return resource;
    }

    private static List<string> Validate(Resource resource)
    {
        var errors = new List<string>();

        if (string.IsNullOrWhiteSpace(resource.Name)) errors.Add("缺少资源名称");
        if (string.IsNullOrWhiteSpace(resource.Description)) errors.Add("缺少资源简介");
        if (string.IsNullOrWhiteSpace(resource.Url)) errors.Add("缺少资源链接");
        if (string.IsNullOrWhiteSpace(resource.Category)) errors.Add("缺少内容分类");
        if (string.IsNullOrWhiteSpace(resource.Type)) errors.Add("缺少资源类型");
        if (resource.Tags.Count == 0) errors.Add("缺少标签");

        return errors;
    }

    private string RecordLabel(FeishuRecord record, string resourceName)
    {
        string name = !string.IsNullOrWhiteSpace(resourceName)
            ? resourceName
            : record.GetText(_config.Fields.Name);

        if (string.IsNullOrWhiteSpace(name))
        {
            name = "未命名投稿";
        }

        return $"{name}（飞书记录 ID：{record.RecordId}）";
    }

    private static TimeZoneInfo FindShanghaiTimeZone()
    {
        // GitHub 的 Ubuntu Runner 使用 IANA 名称；Windows 通常使用 Windows 名称。
        // 两个名字都尝试，使教学程序能在本机和 Actions 中运行。
        foreach (string id in new[] { "Asia/Shanghai", "China Standard Time" })
        {
            try
            {
                return TimeZoneInfo.FindSystemTimeZoneById(id);
            }
            catch (TimeZoneNotFoundException)
            {
            }
        }

        throw new TimeZoneNotFoundException("找不到上海时区配置");
    }
}

internal sealed class FeishuRecord
{
    public required string RecordId { get; init; }
    public long CreatedTime { get; init; }
    public required Dictionary<string, JsonElement> Fields { get; init; }

    public static FeishuRecord FromJson(JsonElement element)
    {
        string recordId = element.TryGetProperty("record_id", out JsonElement idElement)
            ? idElement.GetString() ?? ""
            : "";

        long createdTime = 0;
        if (element.TryGetProperty("created_time", out JsonElement timeElement))
        {
            if (timeElement.ValueKind == JsonValueKind.Number)
            {
                timeElement.TryGetInt64(out createdTime);
            }
            else
            {
                long.TryParse(timeElement.GetString(), out createdTime);
            }
        }

        var fields = new Dictionary<string, JsonElement>();
        if (element.TryGetProperty("fields", out JsonElement fieldsElement) &&
            fieldsElement.ValueKind == JsonValueKind.Object)
        {
            foreach (JsonProperty property in fieldsElement.EnumerateObject())
            {
                fields[property.Name] = property.Value.Clone();
            }
        }

        return new FeishuRecord
        {
            RecordId = recordId,
            CreatedTime = createdTime,
            Fields = fields
        };
    }

    public string GetText(string fieldName)
    {
        return Fields.TryGetValue(fieldName, out JsonElement value)
            ? ValueConverter.Text(value)
            : "";
    }

    public string GetUrl(string fieldName)
    {
        return Fields.TryGetValue(fieldName, out JsonElement value)
            ? ValueConverter.ExtractUrl(value)
            : "";
    }

    public List<string> GetTags(string fieldName)
    {
        return Fields.TryGetValue(fieldName, out JsonElement value)
            ? ValueConverter.Tags(value)
            : [];
    }

    public long GetCreatedTime(string createdTimeField)
    {
        if (CreatedTime > 0)
        {
            // 飞书时间戳可能使用秒或毫秒。统一成毫秒后排序。
            return CreatedTime < 1_000_000_000_000L
                ? CreatedTime * 1000
                : CreatedTime;
        }

        string fieldValue = GetText(createdTimeField);
        if (long.TryParse(fieldValue, out long numericValue))
        {
            return numericValue < 1_000_000_000_000L
                ? numericValue * 1000
                : numericValue;
        }

        return DateTimeOffset.TryParse(fieldValue, out DateTimeOffset parsed)
            ? parsed.ToUnixTimeMilliseconds()
            : 0;
    }
}

internal static partial class ValueConverter
{
    public static string Text(JsonElement value)
    {
        return value.ValueKind switch
        {
            JsonValueKind.String => value.GetString()?.Trim() ?? "",
            JsonValueKind.Number => value.GetRawText(),
            JsonValueKind.True => "true",
            JsonValueKind.False => "false",
            JsonValueKind.Array => string.Join(", ", value.EnumerateArray()
                .Select(Text)
                .Where(item => !string.IsNullOrWhiteSpace(item))),
            JsonValueKind.Object => TextFromObject(value),
            _ => ""
        };
    }

    public static List<string> Tags(JsonElement value)
    {
        if (value.ValueKind == JsonValueKind.Array)
        {
            return value.EnumerateArray()
                .Select(Text)
                .Where(item => !string.IsNullOrWhiteSpace(item))
                .ToList();
        }

        return Text(value)
            .Split([',', '，', '、'], StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)
            .Where(item => !string.IsNullOrWhiteSpace(item))
            .ToList();
    }

    public static string ExtractUrl(JsonElement value)
    {
        // 飞书链接字段可能是字符串、数组，或包含 link/text/url 的对象。
        // 这里递归寻找第一个能够规范化的 URL；如果都不合法，则返回首个候选值，
        // 让上层校验给出“链接格式错误”的明确日志。
        var candidates = new List<string>();
        CollectUrlCandidates(value, candidates);

        foreach (string candidate in candidates)
        {
            string cleaned = ExtractHttpText(candidate);
            if (NormalizeUrl(cleaned) is not null)
            {
                return cleaned;
            }
        }

        return candidates.Count > 0 ? ExtractHttpText(candidates[0]) : "";
    }

    public static string? NormalizeUrl(string? value)
    {
        string cleaned = CleanInvisibleCharacters(value ?? "").Trim();
        if (!Uri.TryCreate(cleaned, UriKind.Absolute, out Uri? uri))
        {
            return null;
        }

        if (uri.Scheme != Uri.UriSchemeHttp && uri.Scheme != Uri.UriSchemeHttps)
        {
            return null;
        }

        return uri.AbsoluteUri;
    }

    private static string TextFromObject(JsonElement value)
    {
        foreach (string key in new[] { "text", "name", "link", "url", "value" })
        {
            if (value.TryGetProperty(key, out JsonElement property))
            {
                string result = Text(property);
                if (!string.IsNullOrWhiteSpace(result))
                {
                    return result;
                }
            }
        }

        return "";
    }

    private static void CollectUrlCandidates(JsonElement value, List<string> candidates)
    {
        switch (value.ValueKind)
        {
            case JsonValueKind.String:
                string text = value.GetString() ?? "";
                if (!string.IsNullOrWhiteSpace(text)) candidates.Add(text);
                break;

            case JsonValueKind.Array:
                foreach (JsonElement item in value.EnumerateArray())
                {
                    CollectUrlCandidates(item, candidates);
                }
                break;

            case JsonValueKind.Object:
                foreach (string key in new[] { "link", "url", "text", "value", "name" })
                {
                    if (value.TryGetProperty(key, out JsonElement property))
                    {
                        CollectUrlCandidates(property, candidates);
                    }
                }
                break;
        }
    }

    private static string ExtractHttpText(string value)
    {
        string cleaned = CleanInvisibleCharacters(value);
        Match match = HttpUrlRegex().Match(cleaned);
        if (!match.Success)
        {
            return "";
        }

        string result = match.Value;

        // 用户可能粘贴“URL提取码：1234”，需要截断状态说明。
        result = ShareCodeRegex().Split(result, 2)[0];
        return result.TrimEnd('，', ',', '。', '；', ';', '、', '）', '】', '》', '>');
    }

    private static string CleanInvisibleCharacters(string value)
    {
        return value
            .Replace("\u200B", "")
            .Replace("\u200C", "")
            .Replace("\u200D", "")
            .Replace("\u2060", "")
            .Replace("\uFEFF", "")
            .Replace('\u00A0', ' ')
            .Replace('\u202F', ' ');
    }

    [GeneratedRegex(@"https?://\S+", RegexOptions.IgnoreCase)]
    private static partial Regex HttpUrlRegex();

    [GeneratedRegex(@"(?=(?:提取码|访问码|密码)[：:])")]
    private static partial Regex ShareCodeRegex();
}

internal static class GitHubActionsOutput
{
    public static async Task WriteAsync(string name, string value)
    {
        string? outputPath = Environment.GetEnvironmentVariable("GITHUB_OUTPUT");

        // 在本地直接运行时没有 GITHUB_OUTPUT，跳过即可；
        // 在 Actions 中，这个变量指向 Runner 创建的特殊临时文件。
        if (string.IsNullOrWhiteSpace(outputPath))
        {
            return;
        }

        // AppendAllTextAsync 必须是追加写。若覆盖写，后一个输出会抹掉前一个。
        await File.AppendAllTextAsync(
            outputPath,
            $"{name}={value}{Environment.NewLine}");
    }
}

internal sealed class ResourceFile
{
    public string UpdatedAt { get; set; } = "";
    public string SubmitUrl { get; set; } = "";
    public string DefaultCover { get; set; } = "";
    public List<Resource> Resources { get; set; } = [];
}

internal sealed class Resource
{
    public string Name { get; set; } = "";
    public string Description { get; set; } = "";
    public string Url { get; set; } = "";
    public string Category { get; set; } = "";
    public string Type { get; set; } = "";
    public List<string> Tags { get; set; } = [];

    // null 时，JsonIgnoreCondition.WhenWritingNull 会让 JSON 完全不出现 cover 字段。
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Cover { get; set; }
}

internal sealed class AcceptedRecord
{
    public string RecordId { get; set; } = "";
    public string Name { get; set; } = "";
    public string Url { get; set; } = "";
}

internal static class JsonOptions
{
    public static readonly JsonSerializerOptions Default = new()
    {
        // C# 的 UpdatedAt 会序列化成 resources.json 所需的 updatedAt。
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        PropertyNameCaseInsensitive = true,
        WriteIndented = true,
        Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping
    };
}
