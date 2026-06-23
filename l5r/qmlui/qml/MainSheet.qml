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

    // Responsive layout (design system §4.4). Below bpCompact the nav
    // sidebar can't share the row with a usable content area, so it
    // collapses behind a hamburger drawer and a slim top app-bar appears.
    // Phones in portrait go compact; tablets / desktop stay wide.
    readonly property bool compact: width < Theme.bpCompact

    // Single source of truth for the active section. Both the fixed
    // sidebar and the drawer sidebar bind their TOC currentIndex to this
    // (one-way), and the scroll-sync timer writes it, so the highlight
    // never desyncs between the two hosted copies of the sidebar.
    property int currentSection: 0

    // Navigate to a section: highlight its TOC row and scroll the sheet
    // to it. Routed through here by every nav source (TOC click, library
    // nudge) so the single currentSection stays authoritative.
    function navigateTo(index) {
        currentSection = index;
        jumpTo(index);
    }

    // Drive the per-clan accent (design system §5): push the active
    // character's clan id into the ClanTheme singleton whenever it
    // changes, so the sidebar accent re-tints while the layout stays
    // put. Guarded for the null first pass; the Connections covers
    // File>New / open / family edit (all routed through clanChanged).
    // Bind the global text-scale multiplier to the user's "Text size"
    // preference. QML singletons can't see context properties, so the
    // binding is installed here (the root sees appSettings) and pushed
    // onto Theme.fontScale; the whole type scale then re-scales live.
    Component.onCompleted: {
        Theme.fontScale = Qt.binding(
            () => appSettings ? appSettings.fontScale : 1.0);
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

    // Compact top app-bar (design system §4.4): shown only below the
    // bpCompact width, where the fixed sidebar is collapsed into navDrawer.
    // It carries the hamburger that opens the drawer plus the character
    // name (the identity block normally pinned in the sidebar), so the
    // player never loses sight of who they're editing. Styled as the same
    // darker-parchment band as the menu bar. On wide layouts it is hidden
    // and collapsed to zero height, so the desktop chrome is unchanged
    // (ApplicationWindow reserves no space for a hidden header).
    header: ToolBar {
        id: compactBar
        visible: root.compact
        height: root.compact ? implicitHeight : 0

        background: Rectangle {
            color: ClanTheme.paperSidebar
            Widgets.RicePaperOverlay {
            }
            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: 1
                color: Theme.divider
                opacity: Theme.dividerOpacity
            }
        }
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: Theme.s2
            anchors.rightMargin: Theme.s3
            spacing: Theme.s2

            // Hamburger: three ink strokes on a transparent button that
            // warms to the clan accent wash on press, matching the menu
            // bar items' feedback language.
            ToolButton {
                id: hamburger
                implicitWidth: 40
                implicitHeight: 40
                padding: 0
                Layout.alignment: Qt.AlignVCenter
                onClicked: navDrawer.open()
                ToolTip.visible: hovered
                ToolTip.text: qsTr("Sections")
                background: Rectangle {
                    radius: 4
                    color: (hamburger.down || hamburger.hovered) ? ClanTheme.selectedBg : "transparent"
                    Behavior on color {
                        ColorAnimation {
                            duration: Theme.durHover
                            easing.type: Easing.OutQuad
                        }
                    }
                }
                // The contentItem fills the button's content area, so the
                // three strokes must be centred within it (both axes) --
                // otherwise they sit top-left and read as misaligned with
                // the name label beside them.
                contentItem: Item {
                    Column {
                        anchors.centerIn: parent
                        spacing: 4
                        Repeater {
                            model: 3
                            delegate: Rectangle {
                                width: 20
                                height: 2
                                radius: 1
                                color: (hamburger.down || hamburger.hovered) ? ClanTheme.primary : Theme.ink
                            }
                        }
                    }
                }
            }

            Label {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignVCenter
                text: (pcProxy && pcProxy.name) ? pcProxy.name : qsTr("Unnamed")
                font.family: Theme.fontDisplay
                font.pixelSize: Theme.fsHeading2
                font.weight: Theme.wSemiBold
                font.letterSpacing: 0.5
                color: Theme.heading
                elide: Text.ElideRight
                verticalAlignment: Text.AlignVCenter
            }
        }
    }

    // Drawer hosting the nav sidebar in compact mode. Slides in from the
    // left edge over the sheet; dismissed by tapping outside, by the back
    // gesture, or by activating a section. Built only when compact so it
    // never intercepts edge swipes on the desktop layout.
    Drawer {
        id: navDrawer
        edge: Qt.LeftEdge
        // Roomy enough for the longest section title, capped so it never
        // swallows the whole phone screen.
        width: Math.min(280, root.width * 0.85)
        height: root.height
        // The fixed sidebar already covers wide layouts; keep the drawer
        // inert (and its content unbuilt) there.
        interactive: root.compact
        dim: true
        // No padding gap, and a parchment background so no grey Fusion
        // panel shows behind / around the sidebar while it slides in.
        padding: 0
        background: Rectangle {
            color: ClanTheme.paperSidebar
        }

        // Loader-gated so the drawer's copy of the sidebar (a second TOC
        // bound to appCtrl.tabs) is only instantiated in compact mode --
        // on desktop the fixed sidebar is the only one built.
        Loader {
            anchors.fill: parent
            active: root.compact
            sourceComponent: Component {
                Widgets.SheetSidebar {
                    currentIndex: root.currentSection
                    onSectionActivated: function (index) {
                        root.navigateTo(index);
                        navDrawer.close();
                    }
                }
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
        if (i >= 0)
            navigateTo(i);
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
        onTriggered: root.currentSection = root.activeSectionFromContentY(flick.contentY)
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

            // ---- Left TOC (fixed, wide layouts only) ----------------------
            // On compact layouts the same SheetSidebar is hosted in
            // navDrawer instead; here it collapses out of the row (zero
            // width) so the sheet gets the full width.
            Widgets.SheetSidebar {
                Layout.preferredWidth: root.compact ? 0 : 220
                Layout.fillHeight: true
                visible: !root.compact
                currentIndex: root.currentSection
                onSectionActivated: function (index) {
                    root.navigateTo(index);
                }
            }

            Rectangle {
                Layout.preferredWidth: 1
                Layout.fillHeight: true
                visible: !root.compact
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
        // Clear the fixed sidebar (220px + 1px divider) on wide layouts;
        // in compact mode there is no sidebar, so span the full width.
        anchors.leftMargin: root.compact ? 0 : 221
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
