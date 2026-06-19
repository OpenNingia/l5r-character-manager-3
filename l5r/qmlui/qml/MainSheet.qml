// Copyright (C) 2014-2026 Daniele Simonetti
// Prototype "scrollable sheet" navigation: every section stacked
// vertically in one long scroll; a left-hand TOC tracks the currently
// visible section and jumps to others on click.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "widgets" as Widgets
import "dialogs" as Dialogs
import Theme 1.0
import ClanTheme 1.0

ApplicationWindow {
    id: root
    width: 1000
    height: 720
    visible: true
    // Null-guard the proxy refs: QML evaluates ApplicationWindow's
    // construction-time bindings before context properties are fully
    // wired, so pcProxy/appCtrl read as null on the first pass and
    // then resettle. Without the guard the engine logs a TypeError on
    // every launch.
    title: pcProxy ? pcProxy.displayTitle : ""
    // The whole client area is parchment now -- no OS-grey desk under
    // the panels. The menubar above is a parchment band too (L5RMenuBar),
    // so the only OS chrome left is the native window frame. The parchment
    // carries a faint wash of the active clan's accent (ClanTheme.paper) so
    // the whole sheet reads in the clan's hue.
    color: ClanTheme.paper

    // Drive the per-clan accent (design system §5): push the active
    // character's clan id into the ClanTheme singleton whenever it
    // changes, so the sidebar accent re-tints while the layout stays
    // put. Guarded for the null first pass; the Connections covers
    // File>New / open / family edit (all routed through clanChanged).
    Component.onCompleted: {
        if (pcProxy)
            ClanTheme.setClan(pcProxy.clanId);
        // First-run nudge: with no datapacks the app is near-useless, so
        // land the user on the Library section (which foregrounds the Core
        // download). Deferred so the section layout has settled and jumpTo
        // reads accurate section y's.
        if (datapacks && !datapacks.hasPacks)
            Qt.callLater(root.jumpToLibrary);
    }
    Connections {
        target: pcProxy
        function onClanChanged() {
            ClanTheme.setClan(pcProxy.clanId);
        }
    }

    menuBar: Widgets.L5RMenuBar {
        Widgets.L5RMenu {
            title: qsTr("&File")
            Widgets.L5RMenuItem {
                text: qsTr("&New")
                // requestFileNew gates on unsaved changes: New discards the
                // autosave recovery file, so a dirty model pops newConfirmDlg
                // first (via fileNewRequiresConfirm) instead of dropping work.
                onTriggered: appCtrl.requestFileNew()
            }
            Widgets.L5RMenuItem {
                text: qsTr("&Open...")
                // requestFileOpen gates on unsaved changes: opening replaces
                // the working character and discards the recovery file, so a
                // dirty model confirms first (via confirmDiscardChanges).
                onTriggered: appCtrl.requestFileOpen()
            }
            Widgets.L5RMenuItem {
                text: qsTr("&Save")
                onTriggered: appCtrl.fileSave()
            }
            Widgets.L5RMenuItem {
                text: qsTr("Save &As...")
                onTriggered: appCtrl.fileSaveAs()
            }
            Widgets.L5RMenuSeparator {
            }
            Widgets.L5RMenuItem {
                text: qsTr("Ex&port as PDF...")
                onTriggered: appCtrl.exportPdfDialog()
            }
            Widgets.L5RMenuItem {
                text: qsTr("Export &NPC Sheet...")
                onTriggered: appCtrl.exportNpcDialog()
            }
            Widgets.L5RMenuSeparator {
            }
            Widgets.L5RMenuItem {
                text: qsTr("&Quit")
                onTriggered: appCtrl.fileQuit()
            }
        }

        // View: one checkable row per hideable section (checked = shown),
        // a discoverable alternative to the sidebar eye. Built from
        // appCtrl.tabs so it can't drift from the section list; the fixed
        // sections (pc_info / about) get no row.
        Widgets.L5RMenu {
            id: viewMenu
            title: qsTr("&View")
            Instantiator {
                model: appCtrl ? appCtrl.tabs : []
                delegate: Widgets.L5RMenuItem {
                    id: viewItem
                    visible: !root.sectionFixed(modelData.id)
                    height: visible ? implicitHeight : 0
                    text: modelData.title
                    checkable: true
                    checked: !root.sectionHidden(modelData.id)
                    onTriggered: appCtrl.setSectionHidden(modelData.id, !checked)
                    // The auto-toggle on click writes `checked` imperatively,
                    // breaking the binding above; re-assert it on every
                    // hiddenSectionsChanged so the tick stays correct whether
                    // toggled here or from the sidebar eye.
                    Connections {
                        target: appCtrl
                        function onHiddenSectionsChanged() {
                            viewItem.checked = !root.sectionHidden(modelData.id);
                        }
                    }
                }
                onObjectAdded: (index, object) => viewMenu.insertItem(index, object)
                onObjectRemoved: (index, object) => viewMenu.removeItem(object)
            }
        }
    }

    // Children of `sheetColumn` are SectionBlock items in the same order
    // as appCtrl.tabs. We use sheetRepeater.itemAt(i) to read each one's
    // y coordinate, which the Column layout supplies for us.
    function sectionY(index) {
        var item = sheetRepeater.itemAt(index);
        return item ? item.y : 0;
    }

    function activeSectionFromContentY(y) {
        // 60px lookahead: a section becomes "active" just before its top
        // hits the viewport top. Reads the live section y's every call,
        // so it stays correct no matter how the content grew -- skills/
        // perks/spells added, rows expanded, window resized. Only called
        // once per scroll, when tocSyncTimer fires at rest, so the live
        // itemAt(i).y reads cost nothing on the scroll path.
        var probe = y + 60;
        var active = 0;
        for (var i = 0; i < sheetRepeater.count; ++i) {
            if (sectionY(i) <= probe) {
                active = i;
            } else {
                break;
            }
        }
        return active;
    }

    function jumpTo(index) {
        var target = sectionY(index);
        var maxY = Math.max(0, flick.contentHeight - flick.height);
        scrollAnim.to = Math.min(target, maxY);
        scrollAnim.restart();
    }

    // Per-character section visibility (the sidebar eye / View menu).
    // Both read appCtrl's notifyable lists, so every binding that calls
    // them re-evaluates when hiddenSectionsChanged fires.
    function sectionHidden(id) {
        return appCtrl ? appCtrl.hiddenSections.indexOf(id) >= 0 : false;
    }
    function sectionFixed(id) {
        return appCtrl ? appCtrl.fixedSections.indexOf(id) >= 0 : false;
    }

    // Index of the Library section in appCtrl.tabs (-1 if absent). Scanned
    // rather than hard-coded so tab reordering can't desync the nudge.
    function libraryIndex() {
        var tabs = appCtrl ? appCtrl.tabs : [];
        for (var i = 0; i < tabs.length; ++i) {
            if (tabs[i].id === "library")
                return i;
        }
        return -1;
    }

    function jumpToLibrary() {
        var i = libraryIndex();
        if (i >= 0) {
            toc.currentIndex = i;
            jumpTo(i);
        }
    }

    // Update the active-section highlight when scrolling goes idle, not
    // during the scroll. Every contentY delta restarts this timer, so
    // while the wheel/touchpad/flick keeps the sheet moving it never
    // fires -- zero work mid-scroll, the frame is never starved. It
    // fires once, ~`interval` ms after the last delta, reading contentY
    // live at that point so it lands on the true resting position.
    // Keyed off contentY rather than Flickable.onMovementEnded so it
    // stays correct for every input type, including mouse-wheel (whose
    // movement signals are unreliable).
    Timer {
        id: tocSyncTimer
        interval: 120
        repeat: false
        onTriggered: toc.currentIndex = root.activeSectionFromContentY(flick.contentY)
    }

    NumberAnimation {
        id: scrollAnim
        target: flick
        property: "contentY"
        duration: 220
        easing.type: Easing.OutQuad
    }

    // Outer Pane owns the parchment background, the rice-paper fibre
    // texture, and the ink-on-paper palette overrides. The palette
    // descends to every Control/Label inside (TOC delegates, section
    // bodies, dialogs) so we don't need to repeat the overrides
    // per-SheetPanel -- the SheetPanel ones become defensive defaults
    // for when a panel is used outside this window (e.g. tests).
    Pane {
        anchors.fill: parent
        padding: 0
        palette.windowText: Theme.ink
        palette.text: Theme.ink
        palette.buttonText: Theme.ink
        palette.base: Theme.parchmentBase
        palette.alternateBase: Theme.parchmentInset
        palette.placeholderText: Theme.inkFaint
        palette.mid: Theme.inkFaint

        background: Rectangle {
            color: ClanTheme.paper
            // Window-wide fibre overlay -- continuous across panels
            // and gutters so the whole sheet feels like one piece of
            // paper.
            Widgets.RicePaperOverlay {
            }
        }

        RowLayout {
            anchors.fill: parent
            spacing: 0

            // ---- Left TOC --------------------------------------------------
            Rectangle {
                Layout.preferredWidth: 220
                Layout.fillHeight: true
                // Slightly darker parchment than the main sheet so the
                // navigation column reads as a distinct zone without
                // breaking the "one document" illusion.
                color: ClanTheme.paperSidebar

                // Same fibre texture as the main sheet so the sidebar
                // reads as the same paper, just a darker shade -- not a
                // flat coloured panel glued onto the document.
                Widgets.RicePaperOverlay {
                }

                ColumnLayout {
                    anchors.fill: parent
                    anchors.topMargin: 14
                    anchors.bottomMargin: 8
                    anchors.leftMargin: 10
                    anchors.rightMargin: 10
                    spacing: 6

                    // ---- Identity block ----------------------------------
                    // Three-line character header above the TOC: name in
                    // burnt-gold display type, clan + rank as a single
                    // secondary line, school italicised underneath. Reads
                    // like the title block of a character sheet rather
                    // than a piece of chrome.
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 1

                        Label {
                            Layout.fillWidth: true
                            text: (pcProxy && pcProxy.name) ? pcProxy.name : qsTr("Unnamed")
                            font.family: Theme.fontDisplay
                            font.pixelSize: 17
                            font.weight: Font.DemiBold
                            font.letterSpacing: 0.5
                            color: Theme.heading
                            elide: Text.ElideRight
                            horizontalAlignment: Text.AlignHCenter
                        }
                        Label {
                            Layout.fillWidth: true
                            readonly property string _clan: (pcProxy && pcProxy.clan) ? pcProxy.clan : ""
                            readonly property int _rank: pcProxy ? pcProxy.progression.rank : 0
                            text: {
                                var clanFmt = _clan ? _clan.charAt(0).toUpperCase() + _clan.slice(1) : qsTr("No Clan");
                                return clanFmt + " — " + qsTr("Rank %1").arg(_rank);
                            }
                            font.pixelSize:Theme.fsBody 
                            font.features: Theme.tabularNumbers
                            color: palette.windowText
                            opacity: 0.85
                            elide: Text.ElideRight
                            horizontalAlignment: Text.AlignHCenter
                        }
                        Label {
                            Layout.fillWidth: true
                            text: (pcProxy && pcProxy.school) ? pcProxy.school : qsTr("No School")
                            font.pixelSize: Theme.fsCaption
                            font.italic: true
                            color: palette.windowText
                            opacity: 0.7
                            elide: Text.ElideRight
                            horizontalAlignment: Text.AlignHCenter
                        }
                    }

                    Widgets.OrnateDivider {
                        Layout.fillWidth: true
                        Layout.topMargin: 4
                        Layout.bottomMargin: 2
                    }

                    ListView {
                        id: toc
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        model: appCtrl ? appCtrl.tabs : []
                        clip: true
                        currentIndex: 0
                        spacing: 2
                        interactive: true
                        boundsBehavior: Flickable.StopAtBounds

                        delegate: ItemDelegate {
                            id: tocDelegate
                            width: ListView.view.width
                            height: 38
                            highlighted: ListView.isCurrentItem
                            // Re-evaluate when appCtrl.hiddenSections changes.
                            readonly property bool sectionIsHidden: root.sectionHidden(modelData.id)
                            readonly property bool sectionIsFixed: root.sectionFixed(modelData.id)
                            onClicked: {
                                // A hidden row is inert, like a disabled
                                // control: clicking its body does nothing.
                                // Only the eye toggle brings it back.
                                if (tocDelegate.sectionIsHidden)
                                    return;
                                toc.currentIndex = index;
                                root.jumpTo(index);
                            }

                            // Strip the default Control background -- without
                            // this override, ItemDelegate paints a palette-
                            // driven fill that reads as flat grey on top of
                            // the parchment sidebar.  Hover gets a warm wash
                            // (lighter parchment), idle is fully transparent
                            // so the sidebar texture shows through.
                            background: Rectangle {
                                // No hover wash on a hidden row -- it's inert,
                                // so it shouldn't invite a click (the eye has
                                // its own hover feedback).
                                color: (tocDelegate.hovered && !tocDelegate.sectionIsHidden) ? Qt.lighter(ClanTheme.paperSidebar, 1.07) : "transparent"
                            }

                            // Active item: accent stripe on the left, accent
                            // icon, accent-tinted label.  Inactive: normal
                            // palette text colours so the OS theme is honoured.
                            Rectangle {
                                anchors.left: parent.left
                                anchors.top: parent.top
                                anchors.bottom: parent.bottom
                                width: 3
                                color: ClanTheme.primary
                                visible: tocDelegate.highlighted
                            }
                            contentItem: RowLayout {
                                spacing: 10
                                // Brush-script kanji; the Hakushū Higerei face
                                // has heavier strokes than a system CJK font
                                // so 20px is comfortable here without crowding
                                // the column.
                                Label {
                                    text: modelData.icon
                                    font.family: Theme.fontKanji
                                    font.pixelSize: 22
                                    Layout.leftMargin: 14
                                    Layout.preferredWidth: 28
                                    horizontalAlignment: Text.AlignHCenter
                                    color: tocDelegate.highlighted ? ClanTheme.primary : palette.windowText
                                    // Dim a hidden section's row so it reads
                                    // as "off" yet stays available to re-show.
                                    opacity: tocDelegate.sectionIsHidden ? 0.35 : (tocDelegate.highlighted ? 1.0 : 0.7)
                                }
                                Label {
                                    text: modelData.title
                                    font.pixelSize: 12
                                    Layout.fillWidth: true
                                    elide: Text.ElideRight
                                    color: tocDelegate.highlighted ? ClanTheme.primary : palette.windowText
                                    font.weight: tocDelegate.highlighted ? Font.DemiBold : Font.Normal
                                    opacity: tocDelegate.sectionIsHidden ? 0.35 : 1.0
                                }

                                // Opportunity badge -- a count of pending
                                // "you unlocked something" actions resolved
                                // in this section (free kiho today; granted
                                // skills / spells / rank-up as those flows
                                // are ported). Accent-blue per the §6.16
                                // positive-action language -- crimson is
                                // reserved for destructive/unmet, so this
                                // reads as an invitation, not an alarm.
                                Rectangle {
                                    readonly property int _count: (pcProxy && pcProxy.opportunityBadges && pcProxy.opportunityBadges[modelData.id] !== undefined) ? pcProxy.opportunityBadges[modelData.id] : 0
                                    visible: _count > 0
                                    Layout.rightMargin: 12
                                    Layout.alignment: Qt.AlignVCenter
                                    implicitWidth: Math.max(18, badgeCount.implicitWidth + 10)
                                    implicitHeight: 18
                                    radius: 9
                                    color: Theme.secondary
                                    Label {
                                        id: badgeCount
                                        anchors.centerIn: parent
                                        text: parent._count
                                        font.family: Theme.fontStat
                                        font.pixelSize: Theme.fsCaption
                                        font.weight: Theme.wSemiBold
                                        font.features: Theme.tabularNumbers
                                        color: Theme.whiteWash
                                    }
                                }

                                // Visibility toggle: a brush 見 ("view")
                                // glyph, matching the kanji section icons.
                                // Shown on hover, or always while the row is
                                // hidden so it can be brought back. Never on
                                // the fixed sections (pc_info / about).
                                ToolButton {
                                    id: eyeBtn
                                    visible: !tocDelegate.sectionIsFixed && (tocDelegate.hovered || tocDelegate.sectionIsHidden)
                                    Layout.rightMargin: 12
                                    Layout.alignment: Qt.AlignVCenter
                                    implicitWidth: 22
                                    implicitHeight: 22
                                    padding: 0
                                    background: Rectangle {
                                        radius: 4
                                        color: eyeBtn.hovered ? Qt.lighter(ClanTheme.paperSidebar, 1.12) : "transparent"
                                    }
                                    contentItem: Label {
                                        text: "見"
                                        font.family: Theme.fontKanji
                                        font.pixelSize: 15
                                        horizontalAlignment: Text.AlignHCenter
                                        verticalAlignment: Text.AlignVCenter
                                        color: tocDelegate.highlighted ? ClanTheme.primary : palette.windowText
                                        opacity: tocDelegate.sectionIsHidden ? 0.9 : (eyeBtn.hovered ? 1.0 : 0.5)
                                    }
                                    onClicked: appCtrl.setSectionHidden(modelData.id, !tocDelegate.sectionIsHidden)
                                    ToolTip.visible: hovered
                                    ToolTip.text: tocDelegate.sectionIsHidden ? qsTr("Show section") : qsTr("Hide section")
                                }
                            }
                        }
                    }
                }
            }

            Rectangle {
                Layout.preferredWidth: 1
                Layout.fillHeight: true
                color: Theme.divider
                opacity: Theme.dividerOpacity
            }

            // ---- Scrollable sheet -----------------------------------------
            Flickable {
                id: flick
                Layout.fillWidth: true
                Layout.fillHeight: true
                contentWidth: width
                contentHeight: sheetColumn.implicitHeight + 32
                clip: true
                boundsBehavior: Flickable.StopAtBounds

                // Flickable's built-in wheel handling advances only a tiny
                // fixed step per notch and ignores the platform wheel
                // speed, so scrolling crawls next to a browser or console.
                // This is the long-standing QTBUG-59261. Work around it by
                // taking the wheel ourselves: a WheelHandler consumes the
                // event (so Flickable's sliver-step never also runs) and we
                // advance contentY by a comfortable amount -- the raw
                // pixelDelta for high-resolution touchpads, or ~one notch
                // worth of lines for a mouse wheel -- clamped to bounds.
                readonly property real _wheelNotchPx: 96   // mouse: px per 120-unit notch
                WheelHandler {
                    target: null
                    acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
                    onWheel: function (ev) {
                        var dy = (ev.pixelDelta.y !== 0) ? ev.pixelDelta.y : ev.angleDelta.y / 120 * flick._wheelNotchPx;
                        var maxY = Math.max(0, flick.contentHeight - flick.height);
                        flick.contentY = Math.max(0, Math.min(maxY, flick.contentY - dy));
                    }
                }

                ScrollBar.vertical: ScrollBar {
                    policy: ScrollBar.AsNeeded
                }

                onContentYChanged: {
                    // Defer the TOC highlight to when scrolling settles
                    // (see tocSyncTimer): restart on every delta so the
                    // update happens once at rest, never mid-scroll. The
                    // guard keeps it from firing during a click-to-jump,
                    // which sets currentIndex directly.
                    if (!scrollAnim.running)
                        tocSyncTimer.restart();
                }

                Column {
                    id: sheetColumn
                    x: 16
                    y: 16
                    width: flick.width - 32
                    spacing: 16

                    Repeater {
                        id: sheetRepeater
                        model: appCtrl ? appCtrl.tabs : []
                        delegate: SectionBlock {
                            width: sheetColumn.width
                            tabId: modelData.id
                            title: modelData.title
                            icon: modelData.icon
                            // Hidden sections collapse out of the scroll; the
                            // Column positioner skips invisible children, so
                            // the spacing closes up too.
                            visible: !root.sectionHidden(modelData.id)
                        }
                    }
                }
            }
        }
    }

    // Transient notices that sit above the sheet, bottom-centred. Driven
    // by the settings proxy's reloadRequired signal (language / front-end
    // changes that only take effect on the next launch). Null-guarded:
    // the preview tool binds appSettings to null.
    Widgets.Toast {
        id: toast
        z: 1000
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: Theme.s5
    }

    Connections {
        target: appSettings
        function onReloadRequired(message) {
            toast.show(message);
        }
    }

    // Datapack operation feedback (install / enable / disable / delete /
    // download). Same transient-toast channel as the settings notices.
    Connections {
        target: datapacks
        function onOperationFinished(ok, message) {
            toast.show(message);
        }
    }

    // Generic purchase/origin feedback from the controller (not enough XP,
    // origin not chosen yet). Replaces the old QMessageBox stopgaps in the
    // modern UI (issues #450 / #448) -- same transient-toast channel.
    Connections {
        target: appCtrl
        function onNotice(message) {
            toast.show(message);
        }
    }

    // Persistent empty-state nudge. Shown whenever no datapack is loaded
    // (active) -- so it also covers "every pack disabled", not just a fresh
    // install. Pinned across the top of the sheet area (past the fixed
    // 220px TOC + 1px divider) so it stays visible while the user scrolls,
    // and bound to datapacks.hasPacks so it vanishes the instant a pack is
    // installed/enabled. Crimson left stripe: important, but informational
    // (it points the way) rather than an error. Parchment-opaque so the
    // sheet scrolls cleanly behind it.
    Rectangle {
        id: nudgeBanner
        z: 900
        visible: datapacks ? !datapacks.hasPacks : false
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.leftMargin: 221
        height: visible ? 44 : 0
        color: Theme.parchmentSidebar

        Rectangle {
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: 3
            color: Theme.accent
        }
        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: 1
            color: Theme.borderSubtle
        }

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: Theme.s4 + 3
            anchors.rightMargin: Theme.s4
            spacing: Theme.s3

            Label {
                Layout.fillWidth: true
                text: qsTr("No datapacks installed — the app needs at least the Core datapack to be useful.")
                font.family: Theme.fontBody
                font.pixelSize: Theme.fsBody
                color: Theme.ink
                elide: Text.ElideRight
            }
            Widgets.L5RButton {
                text: qsTr("Open Library")
                primary: false
                onClicked: root.jumpToLibrary()
            }
        }
    }

    // PDF export feedback. The file itself is opened from the controller on
    // success; here we just surface a transient notice on the sheet.
    Connections {
        target: appCtrl
        function onExportFinished(ok, path) {
            toast.show(ok ? qsTr("Sheet exported.") : qsTr("PDF export failed."));
        }
        // Rank advancement was refused: the player still has unresolved
        // opportunities (school skills, free kiho, ...) which advancing
        // would discard. Remind them to resolve those first.
        function onAdvanceRankBlocked() {
            toast.show(qsTr("Resolve your pending opportunities before advancing rank."));
        }
        // A destructive File action (New / Open) was requested on a dirty
        // model: both discard the autosave recovery snapshot, so confirm
        // before dropping the unsaved work. The action id picks the wording
        // and the slot dispatched on accept.
        function onConfirmDiscardChanges(action) {
            discardConfirmDlg.pendingAction = action;
            discardConfirmDlg.open();
        }
        // An Open was refused because the character's datapacks/books are
        // missing or disabled. List them and point the player at the
        // Library; the working character was left untouched.
        function onLoadFailedMissingBooks(books, path) {
            missingBooksDlg.books = books;
            missingBooksDlg.open();
        }
    }

    // Unsaved-changes guard for the destructive File actions. New and Open
    // both replace the working character and discard the autosave recovery
    // file, so on a dirty model the menu routes through
    // appCtrl.requestFileNew()/requestFileOpen(), which fire
    // confirmDiscardChanges(action) to pop this. Crimson accent per §6.16
    // (destructive action). The body wording, header seal and primary
    // button adapt to the pending action; accepting dispatches to the
    // matching controller slot (which clears / repoints the session store).
    Widgets.L5RDialog {
        id: discardConfirmDlg
        // "new" | "open" -- set by the confirmDiscardChanges handler.
        property string pendingAction: "new"
        readonly property bool _isOpen: pendingAction === "open"

        title: qsTr("Discard unsaved changes?")
        tagline: _isOpen ? qsTr("Open another character")
                         : qsTr("Start a new character")
        seal: _isOpen ? "開" : "新"
        accent: Theme.accent
        accentDark: Theme.accentMuted
        padding: Theme.s6
        acceptText: _isOpen ? qsTr("Discard & Open") : qsTr("Discard & New")
        cancelText: qsTr("Keep editing")
        onAccepted: {
            if (discardConfirmDlg._isOpen)
                appCtrl.fileOpenDialog();
            else
                appCtrl.fileNew();
        }

        Label {
            width: 360
            text: discardConfirmDlg._isOpen
                ? qsTr("This character has changes that are not saved to a "
                    + ".l5r file. Opening another character will discard "
                    + "them. Continue?")
                : qsTr("This character has changes that are not saved to a "
                    + ".l5r file. Starting a new character will discard "
                    + "them. Continue?")
            wrapMode: Text.WordWrap
            font.family: Theme.fontBody
            font.pixelSize: Theme.fsBody
            color: Theme.ink
        }
    }

    // Missing-datapack guard for File > Open. When a character references
    // datapacks/books that are not installed or active, the controller
    // refuses the load (keeping the working character) and fires
    // loadFailedMissingBooks; this lists them and routes the player to the
    // Library to install/enable, then re-open.
    Dialogs.MissingBooksDialog {
        id: missingBooksDlg
        onAccepted: root.jumpToLibrary()
    }
}
