// Copyright (C) 2014-2026 Daniele Simonetti
// Inline chooser for "Buy New Skill" -- replaces the legacy QWidget
// BuyAdvDialog(tag='skill') (l5r/dialogs/advdlg.py) without reusing
// any of its widgets. Pulls the candidate list from
// appCtrl.availableSkillsToBuy() and, on accept, walks the selected
// skill from rank 0 -> 1 via appCtrl.buySkillRank(id) -- the same
// purchase path used to level up an existing skill.
// Lives in qml/dialogs/ alongside the family / school choosers; the
// SkillsSection drives it through `id` + `open()`.
// Visual identity matches InscribePerkDialog: kakemono header with a
// brush seal, parchment + rice-paper background, hand-skinned ComboBox
// in the parchment vocabulary, and custom Cancel/Add buttons.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Theme 1.0

import "../widgets" as Widgets

Dialog {
    id: root
    parent: Overlay.overlay
    anchors.centerIn: Overlay.overlay
    modal: true
    standardButtons: Dialog.NoButton
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent

    width: Math.min(Overlay.overlay ? Overlay.overlay.width - 80 : 520, 520)

    property var _candidates: []
    property string _selectedId: ""

    readonly property color _accent: Theme.secondary

    onAboutToShow: {
        _candidates = appCtrl ? appCtrl.availableSkillsToBuy() : [];
        skillCombo.currentIndex = _candidates.length > 0 ? 0 : -1;
        _selectedId = _candidates.length > 0 ? _candidates[0].id : "";
    }
    function _accept() {
        if (_selectedId && appCtrl)
            appCtrl.buySkillRank(_selectedId);
        root.accept();
    }

    function _currentRecord() {
        if (skillCombo.currentIndex < 0 || skillCombo.currentIndex >= _candidates.length)
            return null;
        return _candidates[skillCombo.currentIndex];
    }

    // --- backplate ------------------------------------------------
    background: Rectangle {
        color: Theme.parchment
        border.color: Theme.borderStrong
        border.width: 1
        radius: 2
        Widgets.RicePaperOverlay {
        }
    }

    // --- header: kakemono band with brush seal --------------------
    header: Item {
        implicitHeight: 64
        Rectangle {
            anchors.fill: parent
            color: Qt.lighter(root._accent, 1.7)
            opacity: 0.55
        }
        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: 1
            color: root._accent
            opacity: 0.45
        }
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 16
            anchors.rightMargin: 16
            spacing: 14

            Label {
                // 修 -- "to cultivate / to train"; reads as the act of
                // learning a discipline, which is what buying a skill
                // models.
                text: "修"
                font.family: Theme.fontKanji
                font.pixelSize: 42
                color: root._accent
                opacity: 0.88
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 0
                Label {
                    text: qsTr("Add a new skill to your repertoire")
                    font.family: Theme.fontDisplay
                    font.pixelSize: Theme.fsHeading1 + 2
                    font.weight: Theme.headingWeight
                    font.letterSpacing: 1.6
                    color: Theme.heading
                }
                Label {
                    text: qsTr("the first rank of any unknown skill costs experience")
                    font.italic: true
                    font.pixelSize: Theme.fsCaption
                    color: Theme.ink
                    opacity: 0.7
                    wrapMode: Text.WordWrap
                }
            }
        }
    }

    // --- body ----------------------------------------------------
    contentItem: ColumnLayout {
        spacing: 14

        // Empty-state notice when no candidates exist (rare -- requires
        // the datapacks to be empty or the character to already know
        // everything in them).
        ColumnLayout {
            visible: root._candidates.length === 0
            Layout.fillWidth: true
            Layout.topMargin: 8
            spacing: 6

            Label {
                Layout.alignment: Qt.AlignHCenter
                text: "修"
                font.family: Theme.fontKanji
                font.pixelSize: 90
                color: root._accent
                opacity: 0.15
            }
            Label {
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                text: qsTr("No further skills are available to learn.")
                font.italic: true
                color: Theme.ink
                opacity: 0.7
            }
        }

        // --- chooser body: combo + read-only details ----------------
        GridLayout {
            visible: root._candidates.length > 0
            Layout.fillWidth: true
            Layout.topMargin: 4
            columns: 2
            columnSpacing: 14
            rowSpacing: 10

            Label {
                text: qsTr("Skill")
                font.family: Theme.fontDisplay
                font.pixelSize: Theme.fsCaption
                font.weight: Theme.headingWeight
                font.letterSpacing: 1.6
                color: Theme.heading
                Layout.preferredWidth: 90
            }
            // Hand-skinned ComboBox -- same parchment vocabulary as the
            // category combo in InscribePerkDialog so this picker feels
            // like the same tool.
            ComboBox {
                id: skillCombo
                Layout.fillWidth: true
                textRole: "name"
                model: root._candidates
                onActivated: function (index) {
                    var rec = root._candidates[index];
                    root._selectedId = rec ? rec.id : "";
                }

                background: Rectangle {
                    color: Theme.parchmentBase
                    border.color: skillCombo.activeFocus ? root._accent : Theme.borderSubtle
                    border.width: 1
                    radius: 3
                    implicitHeight: 30
                }
                contentItem: Label {
                    leftPadding: 10
                    rightPadding: skillCombo.indicator.width + 6
                    text: skillCombo.displayText
                    font.pixelSize:Theme.fsBody 
                    font.weight: Font.DemiBold
                    color: Theme.ink
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideRight
                }
                indicator: Label {
                    x: skillCombo.width - width - 8
                    y: (skillCombo.height - height) / 2
                    text: "▾"
                    font.pixelSize: 12
                    color: Theme.inkMuted
                    opacity: skillCombo.pressed ? 1.0 : 0.85
                }
                popup: Popup {
                    y: skillCombo.height
                    width: skillCombo.width
                    implicitHeight: Math.min(contentItem.implicitHeight + 4, 320)
                    padding: 2
                    background: Rectangle {
                        color: Theme.parchmentBase
                        border.color: Theme.borderStrong
                        border.width: 1
                        radius: 3
                    }
                    contentItem: ListView {
                        clip: true
                        implicitHeight: contentHeight
                        model: skillCombo.popup.visible ? skillCombo.delegateModel : null
                        currentIndex: skillCombo.highlightedIndex
                        ScrollIndicator.vertical: ScrollIndicator {
                        }
                    }
                }
                delegate: ItemDelegate {
                    width: skillCombo.width
                    implicitHeight: 26
                    highlighted: skillCombo.highlightedIndex === index
                    background: Rectangle {
                        color: highlighted ? Qt.rgba(0.224, 0.286, 0.671, 0.12) : "transparent"
                    }
                    contentItem: Label {
                        leftPadding: 10
                        rightPadding: 6
                        text: modelData.name
                        font.pixelSize:Theme.fsBody 
                        color: Theme.ink
                        verticalAlignment: Text.AlignVCenter
                        elide: Text.ElideRight
                    }
                }
            }

            Label {
                text: qsTr("Category")
                font.family: Theme.fontDisplay
                font.pixelSize: Theme.fsCaption
                font.weight: Theme.headingWeight
                font.letterSpacing: 1.6
                color: Theme.heading
            }
            Label {
                Layout.fillWidth: true
                font.italic: true
                color: Theme.ink
                opacity: 0.85
                text: {
                    var rec = root._currentRecord();
                    return rec ? rec.category : "";
                }
            }

            Label {
                text: qsTr("Trait")
                font.family: Theme.fontDisplay
                font.pixelSize: Theme.fsCaption
                font.weight: Theme.headingWeight
                font.letterSpacing: 1.6
                color: Theme.heading
            }
            Label {
                Layout.fillWidth: true
                font.family: Theme.fontDisplay
                font.letterSpacing: 1.4
                font.weight: Font.DemiBold
                color: Theme.heading
                text: {
                    var rec = root._currentRecord();
                    return rec ? rec.trait.toUpperCase() : "";
                }
            }
        }
    }

    // --- footer: Cancel / Add ------------------------------------
    footer: Rectangle {
        implicitHeight: 56
        color: Theme.parchmentSidebar
        Widgets.RicePaperOverlay {
        }
        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            height: 1
            color: Theme.heading
            opacity: 0.35
        }
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 16
            anchors.rightMargin: 16
            spacing: 10

            Item {
                Layout.fillWidth: true
            }

            AbstractButton {
                id: cancelBtn
                implicitHeight: 32
                leftPadding: 18
                rightPadding: 18
                onClicked: root.reject()
                background: Rectangle {
                    radius: 2
                    color: cancelBtn.down ? Qt.darker(Theme.parchmentBase, 1.05)
                                          : (cancelBtn.hovered ? Theme.parchmentBase : "transparent")
                    border.color: Theme.borderStrong
                    border.width: 1
                }
                contentItem: Label {
                    text: qsTr("Cancel")
                    font.family: Theme.fontDisplay
                    font.pixelSize: Theme.fsCaption + 1
                    font.weight: Font.DemiBold
                    font.letterSpacing: 1.3
                    color: Theme.ink
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }

            AbstractButton {
                id: addBtn
                implicitHeight: 32
                leftPadding: 22
                rightPadding: 22
                enabled: root._selectedId.length > 0
                opacity: enabled ? 1.0 : 0.45
                onClicked: root._accept()

                background: Rectangle {
                    radius: 2
                    color: addBtn.down ? Qt.darker(root._accent, 1.25) : root._accent
                    border.color: Qt.darker(root._accent, 1.4)
                    border.width: 1
                }
                contentItem: RowLayout {
                    spacing: 6
                    Label {
                        text: "修"
                        font.family: Theme.fontKanji
                        font.pixelSize: 16
                        color: Theme.parchmentBase
                        opacity: 0.95
                    }
                    Label {
                        text: qsTr("Add")
                        font.family: Theme.fontDisplay
                        font.pixelSize: Theme.fsCaption + 1
                        font.weight: Font.DemiBold
                        font.letterSpacing: 1.6
                        color: Theme.parchmentBase
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }
            }
        }
    }
}
