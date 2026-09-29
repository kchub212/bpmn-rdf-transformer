import BpmnViewer from 'bpmn-js/lib/Viewer.js'

window.initBpmnViewer = function (container, onElementClick) {
  const viewer = new BpmnViewer({ container })

  viewer.on('element.click', (event) => {
    onElementClick(event.element.id, event.element.type)
  })

  return {
    importXml (xml) {
      return viewer.importXML(xml).then(() => {
        viewer.get('canvas').zoom('fit-viewport')
      })
    },
  }
}
