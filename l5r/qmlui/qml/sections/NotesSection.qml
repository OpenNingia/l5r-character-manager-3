// Copyright (C) 2014-2026 Daniele Simonetti
// Notes editor + personal information form. The notes field stores
// rich text HTML (legacy widget's SimpleRichEditor wrote pc.extra_notes
// as HTML); we display it as Text.RichText and write back through
// appCtrl.setNotes when the editor loses focus. The 13 anagraphic /
// family fields are driven by pcProxy.personalInfo (a QVariantMap) and
// mutated through appCtrl.setPersonalInfoField(key, value).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../widgets" as Widgets
import Theme 1.0

ColumnLayout {
    id: section
    spacing: 16

    readonly property var _info: pcProxy ? pcProxy.personalInfo : ({})

    // Pairs of (translated label, model key) -- order matches the
    // legacy widget tab so users see the same form.
    readonly property var _anagraphicFields: [{
            "key": "sex",
            "label": qsTr("Sex")
        }, {
            "key": "age",
            "label": qsTr("Age")
        }, {
            "key": "height",
            "label": qsTr("Height")
        }, {
            "key": "weight",
            "label": qsTr("Weight")
        }, {
            "key": "hair",
            "label": qsTr("Hair")
        }, {
            "key": "eyes",
            "label": qsTr("Eyes")
        }]

    readonly property var _familyFields: [{
            "key": "father",
            "label": qsTr("Father")
        }, {
            "key": "mother",
            "label": qsTr("Mother")
        }, {
            "key": "brothers",
            "label": qsTr("Brothers")
        }, {
            "key": "sisters",
            "label": qsTr("Sisters")
        }, {
            "key": "marsta",
            "label": qsTr("Marital Status")
        }, {
            "key": "spouse",
            "label": qsTr("Spouse")
        }, {
            "key": "childr",
            "label": qsTr("Children")
        }]

    // Notes editor ------------------------------------------------------
    ScrollView {
        Layout.fillWidth: true
        Layout.preferredHeight: 260
        clip: true

        TextArea {
            id: notesEditor
            textFormat: TextEdit.RichText
            wrapMode: TextEdit.Wrap
            placeholderText: qsTr("Notes...")
            selectByMouse: true

            // Re-sync from the model when it changes (load, new, undo).
            // Guarded so user typing doesn't ping-pong through the proxy.
            property bool _syncing: false
            Connections {
                target: pcProxy
                function onNotesChanged() {
                    if (notesEditor.text !== pcProxy.notesHtml) {
                        notesEditor._syncing = true;
                        notesEditor.text = pcProxy.notesHtml;
                        notesEditor._syncing = false;
                    }
                }
            }
            Component.onCompleted: {
                if (pcProxy) {
                    _syncing = true;
                    text = pcProxy.notesHtml;
                    _syncing = false;
                }
            }

            onActiveFocusChanged: {
                if (!activeFocus && !_syncing && appCtrl) {
                    appCtrl.setNotes(text);
                }
            }
        }
    }

    // Personal Information ---------------------------------------------
    Widgets.SheetPanel {
        Layout.fillWidth: true
        title: qsTr("Personal Informations")

        RowLayout {
            width: parent.width
            spacing: 16

            // Anagraphic column
            GridLayout {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignTop
                columns: 2
                columnSpacing: 8
                rowSpacing: 6

                Repeater {
                    model: section._anagraphicFields
                    delegate: RowLayout {
                        Layout.column: 0
                        Layout.row: index
                        Layout.columnSpan: 2
                        Layout.fillWidth: true
                        spacing: 8

                        Label {
                            text: modelData.label
                            Layout.preferredWidth: 80
                            color: palette.windowText
                        }
                        TextField {
                            Layout.fillWidth: true
                            text: section._info[modelData.key] || ""
                            onEditingFinished: {
                                if (appCtrl && text !== (section._info[modelData.key] || "")) {
                                    appCtrl.setPersonalInfoField(modelData.key, text);
                                }
                            }
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillHeight: true
                Layout.preferredWidth: 1
                color: Theme.divider
                opacity: Theme.dividerOpacity
            }

            // Family column
            GridLayout {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignTop
                columns: 2
                columnSpacing: 8
                rowSpacing: 6

                Repeater {
                    model: section._familyFields
                    delegate: RowLayout {
                        Layout.column: 0
                        Layout.row: index
                        Layout.columnSpan: 2
                        Layout.fillWidth: true
                        spacing: 8

                        Label {
                            text: modelData.label
                            Layout.preferredWidth: 110
                            color: palette.windowText
                        }
                        TextField {
                            Layout.fillWidth: true
                            text: section._info[modelData.key] || ""
                            onEditingFinished: {
                                if (appCtrl && text !== (section._info[modelData.key] || "")) {
                                    appCtrl.setPersonalInfoField(modelData.key, text);
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
