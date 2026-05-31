# Introduction Presentation Transcript

- Source deck: docs/introduction.pptx
- Language: en-US
- Total target runtime: under five minutes, including the Live Demo segment
- The Live Demo slide embeds a thirty-second Promotion Video that shows how a traveler experiences the agency app during a disruption, followed by about fifty seconds of live demo narration
- Slide 6 is the final slide of the video (closing summary). Slides 7 through 9 of the deck are intentionally not transcribed

## Slide 1

Hello, and welcome. We are Team H squared, Robert Hsieh and Jet Huang, and the project we are presenting today is called Itinerary in Motion. The single sentence we want you to remember is this: your itinerary listens to the world, and it re-plans itself in seconds. Over the next few minutes we will show you the problem we are solving, the platform we built on top of Solace, and a live demo of it reacting to a real disruption.

## Slide 2

Let us start with the problem. Today, when a travel agency customer, typically a free independent traveler or a custom itinerary traveler, is hit by a flight delay, the only thing they usually receive is a single text message that says their flight is delayed. Everything that happens after that message is the traveler's problem. The hotel check-in, the airport transfer, the tours, and the restaurant bookings are all left unresolved, and the only fallback is the agency hotline, which is exactly the channel that overloads the moment a disruption hits.

Our approach is to give the agency an event-driven platform that they embed into their own product. One disruption turns into a fully re-coordinated itinerary in seconds. A single event fans out in parallel to flights, hotels, tours, and rainy-day alternatives, and the traveler receives one coherent update inside the agency's own app or LINE official account.

This is where Solace matters. The Solace event backbone coordinates every supplier in real time, with no middleware to build. Event Mesh connects everything from the upstream airline feeds down to the downstream notification modules, and Agent Mesh coordinates the modern agentic AI systems that handle airlines, hotels, ground handlers, and the reverse direction as well.

Why does this matter commercially? Our target prospects are the three largest custom itinerary agencies in Taiwan: Lion Travel, Richmond Travel, and Cola Tour. Each of them already owns the customer relationship and the mobile app surface. What they do not own today is a real-time re-planning engine, and that is what we are offering.

## Slide 3

This is the architecture. On the left, an upstream disruption event, a flight status change, arrives at the Solace event broker over the SMF protocol. The broker fans the event out in parallel. One path delivers it to the agency mobile app over WebSocket, so the traveler sees the disruption banner almost immediately. Another path delivers it to Solace Agent Mesh, where the Orchestrator agent dispatches the re-planning work to four specialist agents in parallel: the Flights agent confirms the new status, the Weather agent pulls the destination forecast, the Itinerary agent shifts the affected segments, and the Images agent fetches visuals for the updated plan. The orchestrator merges those results and emits one coherent re-plan event back through the broker, which lands in the same phone-frame UI as a single updated card. Everything you see on this diagram is event-driven and stateless, so the same flow handles one traveler or one thousand travelers without changes.

## Slide 4

Setup is intentionally boring, and that is the point. The full source code and the setup instructions are in the repository linked on this slide. The broker, the Agent Mesh core, the four specialist agents, the fake data generator, and the React phone-frame frontend each come up with a single command. There is no proprietary middleware to install, because Solace is doing that job for us.

## Slide 5

Now the live demo. Before we run it against the live system, here is a thirty-second Promotion Video that shows the traveler's point of view.

Promotion Video script, thirty seconds:

- Zero to five seconds. A traveler is at the gate. Her phone buzzes. The agency app shows: "JL001 to Tokyo is delayed by three hours due to weather."
- Five to twelve seconds. Without her tapping anything, the same card updates: "We have rebooked your airport transfer for the new arrival time, and your hotel has been notified."
- Twelve to twenty seconds. The card expands: "Tomorrow's outdoor tour has rain forecast. We have swapped it for an indoor museum option at the same time slot. Tap to confirm."
- Twenty to twenty-six seconds. She taps confirm. The itinerary timeline animates into its new shape.
- Twenty-six to thirty seconds. Closing line on screen and in voice over: "One disruption. One coherent plan. Powered by Solace."

Now we will run the same flow live. The phone-frame UI is idle, listening on the disruption topic. In the side terminal we publish one event: flight JL001, delayed one hundred eighty minutes, reason weather. Watch the banner appear, watch the four agent steps light up in order, and watch the final card render with the shifted itinerary, the weather headline, and the rebooked ground segment. Our acceptance threshold is thirty seconds end to end.

## Slide 6

To wrap up. One disruption event, one coherent re-plan, delivered straight into the agency's own app. The Solace event backbone and Agent Mesh are doing the heavy lifting, which is why we can offer this to Lion Travel, Richmond Travel, and Cola Tour without asking them to rebuild anything they already own. Thank you for your time. We are happy to take questions, and we are happy to rerun the demo with a different flight number to show that the flow is stateless.
