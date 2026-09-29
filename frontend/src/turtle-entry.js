import { basicSetup, EditorView } from 'codemirror'
import { EditorState, EditorSelection } from '@codemirror/state'
import { turtle } from '@kurrawongai/codemirror-lang-turtle12'

window.initTurtleEditor = function (container, initialText) {
  const view = new EditorView({
    parent: container,
    state: EditorState.create({
      doc: initialText || '',
      extensions: [basicSetup, turtle()],
    }),
  })

  return {
    getText () {
      return view.state.doc.toString()
    },
    setText (text) {
      view.dispatch({
        changes: { from: 0, to: view.state.doc.length, insert: text },
      })
    },
    highlightRange (from, to) {
      view.dispatch({
        selection: EditorSelection.single(from, to),
        scrollIntoView: true,
      })
      view.focus()
    },
  }
}
