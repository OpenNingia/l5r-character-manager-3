// Copyright (C) 2014-2026 Daniele Simonetti
// Navigation sidebar: the character identity block above a table-of-
// contents list of every section. Extracted from MainSheet so the SAME
// content can be hosted in two places depending on window width
// (design system §4.4 responsive layout):
//   - wide  : pinned in the main RowLayout as a fixed 220px column;
//   - compact: inside a left-edge Drawer opened by the top-bar hamburger.
//
// The component is stateless about *which* section is current: the owner
// drives `currentIndex` (one-way) and listens to `sectionActivated(index)`
// for navigable clicks, so both hosted instances stay in lockstep with a
// single source of truth in MainSheet. The Qt context properties
// (pcProxy / appCtrl) are read directly -- they are global to every QML
// file in this UI.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Theme 1.0
import ClanTheme 1.0

Rectangle {
    id: sidebar

    // Driven by the owner; flows to the ListView's currentIndex (one-way).
    property int currentIndex: 0
    // Emitted when a *navigable* (non-hidden) row is clicked. The owner
    // scrolls the sheet and, in compact mode, closes the drawer.
    signal sectionActivated(int index)

    // Slightly darker parchment than the main sheet so the navigation
    // column reads as a distinct zone without breaking the "one document"
    // illusion.
    color: ClanTheme.paperSidebar

    // Ink-on-parchment palette, self-contained. The fixed-sidebar host
    // (MainSheet's Pane) sets these and they descend to children, but the
    // drawer host is a Popup -- a separate palette root that does NOT
    // inherit the Pane's overrides -- so labels reading palette.windowText
    // would otherwise fall back to the system colours there. Declaring the
    // overrides on the component itself makes it render correctly in both
    // hosts (the same defensive pattern as SheetPanel).
    palette.windowText: Theme.ink
    palette.text: Theme.ink
    palette.buttonText: Theme.ink
    palette.base: Theme.parchmentBase
    palette.alternateBase: Theme.parchmentInset
    palette.placeholderText: Theme.inkFaint
    palette.mid: Theme.inkFaint

    // Per-character section visibility (the sidebar eye / View menu).
    // Both read appCtrl's notifyable lists, so every binding that calls
    // them re-evaluates when hiddenSectionsChanged fires.
    function sectionHidden(id) {
        return appCtrl ? appCtrl.hiddenSections.indexOf(id) >= 0 : false;
    }
    function sectionFixed(id) {
        return appCtrl ? appCtrl.fixedSections.indexOf(id) >= 0 : false;
    }

    // Same fibre texture as the main sheet so the sidebar reads as the
    // same paper, just a darker shade -- not a flat coloured panel glued
    // onto the document.
    RicePaperOverlay {
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.topMargin: 14
        anchors.bottomMargin: 8
        anchors.leftMargin: 10
        anchors.rightMargin: 10
        spacing: 6

        // ---- Identity block ----------------------------------
        // Three-line character header above the TOC: name in burnt-gold
        // display type, clan + rank as a single secondary line, school
        // italicised underneath. Reads like the title block of a
        // character sheet rather than a piece of chrome.
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 1

            Label {
                Layout.fillWidth: true
                text: (pcProxy && pcProxy.name) ? pcProxy.name : qsTr("Unnamed")
                font.family: Theme.fontDisplay
                font.pixelSize: Theme.fsHeading1
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
                font.pixelSize: Theme.fsBody
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

        OrnateDivider {
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
            currentIndex: sidebar.currentIndex
            spacing: 2
            interactive: true
            boundsBehavior: Flickable.StopAtBounds

            delegate: ItemDelegate {
                id: tocDelegate
                width: ListView.view.width
                height: 38
                highlighted: ListView.isCurrentItem
                // Re-evaluate when appCtrl.hiddenSections changes.
                readonly property bool sectionIsHidden: sidebar.sectionHidden(modelData.id)
                readonly property bool sectionIsFixed: sidebar.sectionFixed(modelData.id)
                onClicked: {
                    // A hidden row is inert, like a disabled control:
                    // clicking its body does nothing. Only the eye toggle
                    // brings it back.
                    if (tocDelegate.sectionIsHidden)
                        return;
                    sidebar.sectionActivated(index);
                }

                // Strip the default Control background -- without this
                // override, ItemDelegate paints a palette-driven fill that
                // reads as flat grey on top of the parchment sidebar. Hover
                // gets a warm wash (lighter parchment), idle is fully
                // transparent so the sidebar texture shows through.
                background: Rectangle {
                    // No hover wash on a hidden row -- it's inert, so it
                    // shouldn't invite a click (the eye has its own hover
                    // feedback).
                    color: (tocDelegate.hovered && !tocDelegate.sectionIsHidden) ? Qt.lighter(ClanTheme.paperSidebar, 1.07) : "transparent"
                }

                // Active item: accent stripe on the left, accent icon,
                // accent-tinted label. Inactive: normal palette text
                // colours so the OS theme is honoured.
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
                    // Brush-script kanji; the Hakushū Higerei face has
                    // heavier strokes than a system CJK font so 20px is
                    // comfortable here without crowding the column.
                    Label {
                        text: modelData.icon
                        font.family: Theme.fontKanji
                        font.pixelSize: 22
                        Layout.leftMargin: 14
                        Layout.preferredWidth: 28
                        horizontalAlignment: Text.AlignHCenter
                        color: tocDelegate.highlighted ? ClanTheme.primary : palette.windowText
                        // Dim a hidden section's row so it reads as "off"
                        // yet stays available to re-show.
                        opacity: tocDelegate.sectionIsHidden ? 0.35 : (tocDelegate.highlighted ? 1.0 : 0.7)
                    }
                    Label {
                        text: modelData.title
                        font.pixelSize: Theme.fsBodySmall
                        Layout.fillWidth: true
                        elide: Text.ElideRight
                        color: tocDelegate.highlighted ? ClanTheme.primary : palette.windowText
                        font.weight: tocDelegate.highlighted ? Font.DemiBold : Font.Normal
                        opacity: tocDelegate.sectionIsHidden ? 0.35 : 1.0
                    }

                    // Opportunity badge -- a count of pending "you unlocked
                    // something" actions resolved in this section (free kiho
                    // today; granted skills / spells / rank-up as those
                    // flows are ported). Accent-blue per the §6.16
                    // positive-action language -- crimson is reserved for
                    // destructive/unmet, so this reads as an invitation,
                    // not an alarm.
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

                    // Visibility toggle: a brush 見 ("view") glyph, matching
                    // the kanji section icons. Shown on hover, or always
                    // while the row is hidden so it can be brought back.
                    // Never on the fixed sections (pc_info / about).
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
