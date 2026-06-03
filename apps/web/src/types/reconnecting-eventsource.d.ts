declare module "reconnecting-eventsource" {
  export default class ReconnectingEventSource extends EventSource {
    constructor(url: string | URL, eventSourceInitDict?: EventSourceInit);
  }
}
