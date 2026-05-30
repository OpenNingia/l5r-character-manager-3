// Copyright (C) 2014-2026 Daniele Simonetti
// Prototype "scrollable sheet" navigation: every section stacked
// vertically in one long scroll; a left-hand TOC tracks the currently
// visible section and jumps to others on click.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "widgets" as Widgets
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
    Component.onCompleted: if (pcProxy)
        ClanTheme.setClan(pcProxy.clanId)
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
                onTriggered: appCtrl.fileNew()
            }
            Widgets.L5RMenuItem {
                text: qsTr("&Open...")
                onTriggered: appCtrl.fileOpenDialog()
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
                            onClicked: {
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
                                color: tocDelegate.hovered ? Qt.lighter(ClanTheme.paperSidebar, 1.07) : "transparent"
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
                                    opacity: tocDelegate.highlighted ? 1.0 : 0.7
                                }
                                Label {
                                    text: modelData.title
                                    font.pixelSize: 12
                                    Layout.fillWidth: true
                                    elide: Text.ElideRight
                                    color: tocDelegate.highlighted ? ClanTheme.primary : palette.windowText
                                    font.weight: tocDelegate.highlighted ? Font.DemiBold : Font.Normal
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

    // PDF export feedback. The file itself is opened from the controller on
    // success; here we just surface a transient notice on the sheet.
    Connections {
        target: appCtrl
        function onExportFinished(ok, path) {
            toast.show(ok ? qsTr("Sheet exported.") : qsTr("PDF export failed."));
        }
    }
}
