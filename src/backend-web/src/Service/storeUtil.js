import store  from 'store';

const TOKEN_KEY = 'token';
const USERINFO_KEY = 'userinfo';

const createStore = (key) => {
  return {
    get: () => {
      return store.get(key);
    },
    set: (v) => {
      store.set(key, v);
    },
    remove: () => {
      store.remove(key);
    }
  }
}

export const tokenStore = createStore(TOKEN_KEY);
export const userInfoStore = createStore(USERINFO_KEY);
