' Loads one data file: live copy first, then the last good copy on this Roku,
' then the copy bundled with the app.

sub init()
    m.top.functionName = "load"
end sub

sub load()
    source = readBestCopy(m.top.path)
    if source <> invalid
        data = source.data
        if data.version <> invalid then m.top.version = data.version
        if data.items <> invalid
            m.top.content = buildContent(data.items, source.base)
            m.top.nextPath = data["next"]
        end if
    end if
    m.top.done = true
end sub

function readBestCopy(path as string) as object
    base = FeedBaseUrl()
    cacheFile = "cachefs:/" + path.Replace("/", "_")

    if base <> ""
        text = fetchText(base + path)
        data = parseObject(text)
        if data <> invalid
            WriteAsciiFile(cacheFile, text)
            return { data: data, base: base }
        end if

        data = parseObject(ReadAsciiFile(cacheFile))
        if data <> invalid then return { data: data, base: base }
    end if

    data = parseObject(ReadAsciiFile("pkg:/data/" + path))
    if data <> invalid then return { data: data, base: "pkg:/data/" }
    return invalid
end function

function parseObject(text as string) as object
    if text = "" then return invalid
    data = ParseJson(text)
    if type(data) <> "roAssociativeArray" then return invalid
    return data
end function

function fetchText(url as string) as string
    port = CreateObject("roMessagePort")
    transfer = CreateObject("roUrlTransfer")
    transfer.SetMessagePort(port)
    transfer.SetUrl(url)
    transfer.SetCertificatesFile("common:/certs/ca-bundle.crt")
    transfer.InitClientCertificates()
    transfer.EnableEncodings(true)
    if not transfer.AsyncGetToString() then return ""

    msg = wait(15000, port)
    if type(msg) = "roUrlEvent" and msg.GetResponseCode() = 200 then return msg.GetString()
    transfer.AsyncCancel()
    return ""
end function

function buildContent(items as object, base as string) as object
    root = CreateObject("roSGNode", "ContentNode")
    for each item in items
        node = root.CreateChild("ContentNode")
        thumbId = item.id
        if item.kind = "playlist" then thumbId = item.thumbId

        ' mqdefault is true 16:9. hqdefault is 4:3 and is what Shorts need,
        ' because cropping its black bars leaves the vertical picture.
        thumbFile = "mqdefault.jpg"
        if item.kind = "short" then thumbFile = "hqdefault.jpg"

        node.HDPosterUrl = "https://i.ytimg.com/vi/" + thumbId + "/" + thumbFile
        listPath = ""
        if item.list <> invalid then listPath = item.list
        node.addFields({
            itemId: item.id,
            kind: item.kind,
            titleUri: base + item.titleImage,
            listPath: listPath
        })
    end for
    return root
end function
