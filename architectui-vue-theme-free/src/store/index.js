import Vue from 'vue'
import Vuex from 'vuex'

import { login, register, getModules } from '@/api'
import { isValidJwt, EventBus } from '@/utils'

Vue.use(Vuex);

const state = {
    // single source of data
    // surveys: [],
    // currentSurvey: {},
    user: {},
    jwt: '',
    modules: {},
    current_module: "",
}


const actions = {
    // asynchronous operations
    async login(context, userData) {
        context.commit('setUserData', { userData })
        return login(userData).then(
            (response) => {
                context.commit('setJwtToken', { jwt: response.data });
                return getModules();
            })
            .then((response) => context.commit('setModules', response.data.modules))
            .catch((error) => {
                console.log('Error Authenticating: ', error);
                EventBus.$emit('failedAuthentication', error);
                throw error;
            })
    },
    register(context, userData) {
        context.commit('setUserData', { userData })
        return register(userData)
            .then(context.dispatch('login', userData))
            .catch(error => {
                console.log('Error Registering: ', error)
                EventBus.$emit('failedRegistering: ', error)
            })
    },
    changeCurrentModule(context, module){
        context.commit('setCurrentModule', module);
    }
}

const mutations = {
    // isolated data mutations
    setUserData(state, payload) {
        console.log('setUserData payload = ', payload)
        state.userData = payload.userData
    },
    setJwtToken(state, payload) {
        console.log('setJwtToken payload = ', payload)
        localStorage.token = payload.jwt.token
        state.jwt = payload.jwt
    },
    setModules(state, payload){
        console.log('setModules payload = ', payload)
        state.modules = payload
    },
    setCurrentModule(state, payload){
        console.log('setCurrentModule payload = ', payload)
        state.current_module = payload;
    }
}

const getters = {
    // reusable data accessors
    isAuthenticated(state) {
        return isValidJwt(state.jwt.token)
    },
    getSidebarMenu(state){
        return state.modules
    },
    getAppMenuModules(state){
        return state.modules
    },
    getModuleSidebars(state){
        return state.current_module.sidebars
    }
}

const store = new Vuex.Store({
    state,
    actions,
    mutations,
    getters
})

export default store