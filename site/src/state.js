// A minimal store. Subscribers receive the new state and the changed keys.

export function createStore(initial) {
  let state = initial;
  const subscribers = new Set();
  return {
    get: () => state,
    set(patch) {
      const changed = Object.keys(patch).filter((key) => patch[key] !== state[key]);
      if (!changed.length) return;
      state = { ...state, ...patch };
      for (const subscriber of subscribers) subscriber(state, new Set(changed));
    },
    subscribe(subscriber) {
      subscribers.add(subscriber);
      return () => subscribers.delete(subscriber);
    },
  };
}
