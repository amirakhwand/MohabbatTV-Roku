sub init()
    m.placeholder = m.top.findNode("placeholder")
    m.thumb = m.top.findNode("thumb")
    m.title = m.top.findNode("title")
end sub

sub onContent()
    content = m.top.itemContent
    if content = invalid then return
    m.thumb.uri = content.HDPosterUrl
    m.title.uri = content.titleUri
end sub

sub onLayout()
    ' Title images are always 92px tall, and 10px separates them from the picture.
    thumbHeight = m.top.height - 102
    m.placeholder.width = m.top.width
    m.placeholder.height = thumbHeight
    m.thumb.width = m.top.width
    m.thumb.height = thumbHeight
    m.title.width = m.top.width
    m.title.height = 92
    m.title.translation = [0, thumbHeight + 10]
end sub
