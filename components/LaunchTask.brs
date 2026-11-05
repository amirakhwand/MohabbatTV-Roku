' Opens a video in the official YouTube app (Roku channel 837) by posting to
' this Roku's own control port. Roku's certification rules are reported to
' forbid this in store apps, so it suits a sideloaded build only.

sub init()
    m.top.functionName = "launchYouTube"
end sub

sub launchYouTube()
    ip = deviceIp()
    if ip = ""
        m.top.failed = true
        return
    end if

    transfer = CreateObject("roUrlTransfer")
    transfer.SetUrl("http://" + ip + ":8060/launch/837?contentId=" + m.top.videoId + "&mediaType=shortFormVideo")
    status = transfer.PostFromString("")
    if status < 200 or status >= 300 then m.top.failed = true
end sub

function deviceIp() as string
    addresses = CreateObject("roDeviceInfo").GetIPAddrs()
    for each networkInterface in addresses
        return addresses[networkInterface]
    end for
    return ""
end function
