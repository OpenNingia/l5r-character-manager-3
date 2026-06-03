// Copyright (C) 2014-2026 Daniele Simonetti
// Design-system search bar (§6.6): a paper-light inkwell with a leading
// magnifier glyph and an italic placeholder, gold focus border. Replaces
// the inline "magnifier + bare TextField" search slug in the perk dialog.
//
//   text        -- two-way alias of the input text (read it, or bind)
//   placeholder -- placeholder string (rendered italic, ink-faint)
//   textChanged -- alias change signal; use onTextChanged to react
//
// Usage:
//   Widgets.L5RSearchField {
//       Layout.fillWidth: true
//       placeholder: qsTr("seek by name…")
//       onTextChanged: model.filter = text
//   }
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Theme 1.0

Rectangle {
    id: root
    property alias text: field.text
    property string placeholder: ""

    implicitHeight: 36
    implicitWidth: 160
    color: Theme.parchmentBase          // paper-light (§6.5/§6.6)
    border.width: 1
    border.color: field.activeFocus ? Theme.heading : Theme.borderSubtle  // focus = gold
    radius: 2

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 10
        anchors.rightMargin: 10
        spacing: 8

        Label {
            text: "⌕"
            font.pixelSize: 14
            color: Theme.inkFaint
            Layout.alignment: Qt.AlignVCenter
        }
        TextField {
            id: field
            Layout.fillWidth: true
            placeholderText: root.placeholder
            background: Item {}          // the wrapping Rectangle is the field
            padding: 0
            font.family: Theme.fontBody
            font.pixelSize: Theme.fsBody
            font.italic: text.length === 0
            color: Theme.ink
            placeholderTextColor: Theme.inkFaint
            verticalAlignment: Text.AlignVCenter
        }
    }
}
