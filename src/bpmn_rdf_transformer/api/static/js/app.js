// Block K frontend: BPMN upload, RDF editing/highlighting, and BPMN
// download, all driven by the Flask API built in Block J.

const state = {
  graphId: null,
  currentBpmnXml: null,
}

class ApiError extends Error {
  constructor (message, type) {
    super(message)
    this.type = type
  }
}

// Shared handling for every backend call. The backend always returns
// { error, type } JSON on failure (400/404/422/502/500 alike), so one
// helper covers all of them - see Block J's error handlers.
async function apiFetch (url, options) {
  let response
  try {
    response = await fetch(url, options)
  } catch (err) {
    throw new ApiError(err.message, 'NetworkError')
  }

  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new ApiError(body ? body.error : 'Unbekannter Fehler.', body ? body.type : 'Unknown')
  }

  return response
}

function onElementClick (elementId, elementType) {
  const text = turtleEditor.getText()
  const needle = `"${elementId}"`
  const offset = text.indexOf(needle)

  if (offset === -1) {
    showStatus(`Kein passender RDF-Block für ${elementType} (${elementId}) gefunden.`)
    return
  }

  turtleEditor.highlightRange(offset, offset + needle.length)
  showStatus(`${elementType} (${elementId}) im RDF markiert.`, 'success')
}

const bpmnViewer = window.initBpmnViewer(document.getElementById('bpmn-container'), onElementClick)
const turtleEditor = window.initTurtleEditor(
  document.getElementById('turtle-container'),
  '# Upload a BPMN file to see its RDF representation.\n'
)

const fileInput = document.getElementById('file-input')
const uploadButton = document.getElementById('upload-button')
const applyButton = document.getElementById('apply-button')
const resetButton = document.getElementById('reset-button')
const downloadButton = document.getElementById('download-button')
const statusEl = document.getElementById('status')

function showStatus (message, kind) {
  statusEl.textContent = message
  statusEl.classList.remove('status-error', 'status-success')
  if (kind === 'error' || kind === 'success') {
    statusEl.classList.add(`status-${kind}`)
  }
}

function loadTurtle (text) {
  turtleEditor.setText(text)
}

function requireGraphId () {
  if (!state.graphId) {
    showStatus('Bitte zuerst eine BPMN-Datei hochladen.')
    return false
  }
  return true
}

async function fetchAndLoadRdf () {
  const rdfResponse = await apiFetch(`/api/processes/${state.graphId}/rdf`)
  const turtleText = await rdfResponse.text()
  loadTurtle(turtleText)
}

async function handleUpload () {
  const file = fileInput.files[0]
  if (!file) {
    showStatus('Bitte zuerst eine BPMN-Datei auswählen.')
    return
  }

  const formData = new FormData()
  formData.append('file', file)

  let body
  try {
    const response = await apiFetch('/api/processes', { method: 'POST', body: formData })
    body = await response.json()
  } catch (err) {
    showStatus(`${err.type}: ${err.message}`, 'error')
    return
  }

  state.graphId = body.graph_id
  state.currentBpmnXml = body.bpmn_xml

  await bpmnViewer.importXml(state.currentBpmnXml)
  await fetchAndLoadRdf()

  const warningsText = body.warnings && body.warnings.length
    ? `Hochgeladen. Warnungen: ${body.warnings.join('; ')}`
    : 'Hochgeladen. Keine Warnungen.'
  showStatus(warningsText, 'success')
}

async function handleApply () {
  if (!requireGraphId()) {
    return
  }

  const text = turtleEditor.getText()

  let body
  try {
    const response = await apiFetch(`/api/processes/${state.graphId}/rdf`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ turtle: text }),
    })
    body = await response.json()
  } catch (err) {
    showStatus(`${err.type}: ${err.message}`, 'error')
    return
  }

  // The RDF change and BPMN update already succeeded at this point.
  state.currentBpmnXml = body.bpmn_xml
  await bpmnViewer.importXml(state.currentBpmnXml)

  const warningsText = body.warnings && body.warnings.length
    ? `Änderungen übernommen. Warnungen: ${body.warnings.join('; ')}`
    : 'Änderungen übernommen. Keine Warnungen.'

  // Re-fetch the actual stored/enriched RDF so the editor reflects Fuseki,
  // not just what was submitted. A failure here is a separate "refresh"
  // problem, not an Apply failure - the change itself already succeeded.
  try {
    await fetchAndLoadRdf()
    showStatus(warningsText, 'success')
  } catch (err) {
    showStatus(
      `${warningsText} (Hinweis: Aktualisierung der Anzeige fehlgeschlagen - ${err.type}: ${err.message})`,
      'error'
    )
  }
}

async function handleReset () {
  if (!requireGraphId()) {
    return
  }

  try {
    await fetchAndLoadRdf()
    showStatus('RDF zurückgesetzt.', 'success')
  } catch (err) {
    showStatus(`${err.type}: ${err.message}`, 'error')
  }
}

function handleDownload () {
  if (!state.currentBpmnXml) {
    showStatus('Kein BPMN zum Herunterladen vorhanden.')
    return
  }

  const blob = new Blob([state.currentBpmnXml], { type: 'application/xml' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'process.bpmn'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

uploadButton.addEventListener('click', handleUpload)
applyButton.addEventListener('click', handleApply)
resetButton.addEventListener('click', handleReset)
downloadButton.addEventListener('click', handleDownload)
