from bpmn_rdf_transformer.model.process import StartEvent, Task, ExclusiveGateway, Process, SequenceFlow

def test_exclusive_gateway_equality():
   gateway1 = ExclusiveGateway(id="Gateway1", name="Decision")
   gateway2 = ExclusiveGateway(id="Gateway1", name="Decision")
   gateway3 = ExclusiveGateway(id="Gateway2", name="Decision")

   assert gateway1 == gateway2
   assert gateway1 != gateway3

def test_start_event_equality():
   event1=StartEvent(id="StartEvent1", name="StartEvent1")
   event2=StartEvent(id="StartEvent1", name="StartEvent1")
   event3=StartEvent(id="StartEvent2", name="StartEvent1")

   assert  event1 == event2
   assert event1 != event3

def test_task_default_name_is_none():
   task = Task(id="Task1")
   assert task.name is None

def test_process_starts_empty_and_can_add_items():
   p = Process(id="Process1")
   assert p.nodes == {}
   assert p.sequence_flows == []

   p.nodes["Task1"] = Task(id="Task1")

   p.sequence_flows.append(SequenceFlow(id="Flow_1",source_ref="a", target_ref="b"))
   assert len(p.nodes) == 1
   assert len(p.sequence_flows) == 1


