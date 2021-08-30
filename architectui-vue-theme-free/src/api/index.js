import axios from 'axios'

const API_URL = 'http://localhost:5000'


axios.defaults.headers.common['Access-Control-Allow-Origin'] = '*';

export function login (userData) {
    return axios.post(
        `${API_URL}/api/auth/login`,
        userData, 
        {
            headers: {
                'Content-Type': 'application/json;charset=UTF-8',
            },
        }
    )
}
  
export function register (userData) {
    return axios.post(`${API_URL}/api/auth/register`, userData)
}

export function getModules(){
    return axios.get(`${API_URL}/api/admin/modules`,{
        headers: {
            'Content-Type': 'application/json;charset=UTF-8',
        }
    })
}