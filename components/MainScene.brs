sub init()
    m.top.backgroundColor = "0x0F0F0FFF"
    m.top.backgroundURI = ""

    m.tabNames = ["videos", "live", "shorts", "playlists"]
    m.tabPosters = []
    for i = 0 to 3
        m.tabPosters.Push(m.top.findNode("tab" + i.ToStr()))
    end for
    m.underline = m.top.findNode("tabUnderline")
    m.grid = m.top.findNode("grid")
    m.error = m.top.findNode("error")

    m.tab = 0
    m.inPlaylist = false
    m.saved = invalid
    m.focusArea = "tabs"
    m.requestId = 0
    m.loading = false
    m.nextPath = ""
    m.restoreId = ""
    m.version = ""

    m.grid.observeField("itemSelected", "onItemSelected")
    m.grid.observeField("itemFocused", "onItemFocused")
    m.top.findNode("errorTimer").observeField("fire", "onErrorTimer")
    pollTimer = m.top.findNode("pollTimer")
    pollTimer.observeField("fire", "checkForUpdates")
    pollTimer.control = "start"

    checkForUpdates()
    selectTab(0)
    m.top.setFocus(true)
end sub

' ---------- Tabs and lists ----------

sub selectTab(index as integer)
    m.tab = index
    m.inPlaylist = false
    m.saved = invalid
    for i = 0 to 3
        if i = index
            m.tabPosters[i].blendColor = "0xFFFFFFFF"
        else
            m.tabPosters[i].blendColor = "0x808080FF"
        end if
    end for
    m.underline.translation = [index * 300, 62]
    configureGrid(m.tabNames[index] = "shorts")
    loadList(currentTabPath(), false)
end sub

function currentTabPath() as string
    return "tabs/" + m.tabNames[m.tab] + "-0.json"
end function

sub configureGrid(isShorts as boolean)
    if isShorts
        m.grid.numColumns = 6
        m.grid.numRows = 1
        m.grid.itemSize = [270, 582]
    else
        m.grid.numColumns = 4
        m.grid.numRows = 2
        m.grid.itemSize = [420, 338]
    end if
    m.grid.itemSpacing = [30, 30]
end sub

sub loadList(path as string, append as boolean)
    m.requestId = m.requestId + 1
    m.loading = true
    m.appendResult = append
    task = CreateObject("roSGNode", "ContentTask")
    task.path = path
    task.requestId = m.requestId
    task.observeField("done", "onListLoaded")
    task.control = "run"
    m.listTask = task
end sub

sub onListLoaded(event as object)
    task = event.getRoSGNode()
    if task.requestId <> m.requestId then return
    m.loading = false
    m.nextPath = task.nextPath

    if task.content = invalid
        if not m.appendResult then m.grid.content = CreateObject("roSGNode", "ContentNode")
    else if m.appendResult and m.grid.content <> invalid
        m.grid.content.appendChildren(task.content.getChildren(-1, 0))
    else
        m.grid.content = task.content
        restoreFocus()
    end if

    if m.focusArea = "grid"
        if contentCount() > 0
            m.grid.setFocus(true)
        else
            focusTabs()
        end if
    end if
end sub

sub restoreFocus()
    if m.restoreId = "" then return
    children = m.grid.content.getChildren(-1, 0)
    for i = 0 to children.Count() - 1
        if children[i].itemId = m.restoreId
            m.grid.jumpToItem = i
            exit for
        end if
    end for
    m.restoreId = ""
end sub

function contentCount() as integer
    if m.grid.content = invalid then return 0
    return m.grid.content.getChildCount()
end function

sub onItemFocused()
    remaining = contentCount() - m.grid.itemFocused
    if remaining <= 8 and m.nextPath <> "" and not m.loading
        loadList(m.nextPath, true)
    end if
end sub

sub onItemSelected()
    item = m.grid.content.getChild(m.grid.itemSelected)
    if item = invalid then return
    if item.kind = "playlist"
        openPlaylist(item)
    else
        launchVideo(item.itemId)
    end if
end sub

sub openPlaylist(item as object)
    m.saved = { content: m.grid.content, focus: m.grid.itemFocused, nextPath: m.nextPath }
    m.inPlaylist = true
    m.grid.content = CreateObject("roSGNode", "ContentNode")
    loadList(item.listPath, false)
end sub

sub closePlaylist()
    m.requestId = m.requestId + 1
    m.loading = false
    m.inPlaylist = false
    m.grid.content = m.saved.content
    m.grid.jumpToItem = m.saved.focus
    m.nextPath = m.saved.nextPath
    m.saved = invalid
end sub

' ---------- Playback ----------

sub launchVideo(videoId as string)
    task = CreateObject("roSGNode", "LaunchTask")
    task.videoId = videoId
    task.observeField("failed", "onLaunchFailed")
    task.control = "run"
    m.launchTask = task
end sub

sub onLaunchFailed()
    m.error.visible = true
    m.top.findNode("errorTimer").control = "start"
end sub

sub onErrorTimer()
    m.error.visible = false
end sub

' ---------- Automatic updates ----------

sub checkForUpdates()
    task = CreateObject("roSGNode", "ContentTask")
    task.path = "feed.json"
    task.observeField("done", "onFeedChecked")
    task.control = "run"
    m.pollTask = task
end sub

sub onFeedChecked(event as object)
    version = event.getRoSGNode().version
    if version = "" or version = m.version then return
    isFirstCheck = (m.version = "")
    m.version = version
    if isFirstCheck then return

    ' Viewers deep in a list keep their place. They get the new list on their
    ' next tab change, because every tab change loads fresh data.
    if m.inPlaylist or m.grid.itemFocused >= 30 then return
    if contentCount() > 0
        focused = m.grid.content.getChild(m.grid.itemFocused)
        if focused <> invalid then m.restoreId = focused.itemId
    end if
    loadList(currentTabPath(), false)
end sub

' ---------- Remote control ----------

sub focusTabs()
    m.focusArea = "tabs"
    m.top.setFocus(true)
end sub

function onKeyEvent(key as string, press as boolean) as boolean
    if not press then return false

    if m.focusArea = "tabs"
        if key = "right" and m.tab < 3
            selectTab(m.tab + 1)
            return true
        else if key = "left" and m.tab > 0
            selectTab(m.tab - 1)
            return true
        else if (key = "down" or key = "OK") and contentCount() > 0
            m.focusArea = "grid"
            m.grid.setFocus(true)
            return true
        else if key = "back" and m.inPlaylist
            closePlaylist()
            return true
        end if
        return false
    end if

    if key = "up"
        focusTabs()
        return true
    else if key = "back"
        if m.inPlaylist
            closePlaylist()
        else
            focusTabs()
        end if
        return true
    end if
    return false
end function
