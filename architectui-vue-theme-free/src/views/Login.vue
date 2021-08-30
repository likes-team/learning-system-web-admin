<template>
  <div>
    <div class="h-100 bg-plum-plate bg-animation">
      <div class="d-flex h-100 justify-content-center align-items-center">
        <b-col md="8" class="mx-auto app-login-box">
          <div class="app-logo-inverse mx-auto mb-3" />

          <div class="modal-dialog w-100 mx-auto">
            <div class="modal-content">
              <div class="modal-body">
                <div class="h5 modal-title text-center">
                  <h4 class="mt-2">
                    <div>Welcome to</div>
                    <span>Likes Application Framework</span>
                    <p class="text-danger">{{ errorMsg }}</p>
                  </h4>
                </div>
                <b-form-group
                  label-for="inp_username"
                  description="We'll never share your email with anyone else."
                >
                  <b-form-input
                    v-model="username"
                    id="inp_username"
                    type="text"
                    required
                    placeholder="Enter username..."
                  >
                  </b-form-input>
                </b-form-group>
                <b-form-group label-for="inp_password">
                  <b-form-input
                    v-model="password"
                    id="inp_password"
                    type="password"
                    required
                    placeholder="Enter password..."
                  >
                  </b-form-input>
                </b-form-group>
                <!-- <b-form-checkbox name="check" id="exampleCheck">
                                    Keep me logged in
                                </b-form-checkbox> -->
                <div class="divider" />
                <h6 class="mb-0">
                  No account?
                  <a href="javascript:void(0);" class="text-primary"
                    >Sign up now</a
                  >
                </h6>
              </div>
              <div class="modal-footer clearfix">
                <!-- <div class="float-left">
                                    <a href="javascript:void(0);" class="btn-lg btn btn-link">Recover
                                        Password</a>
                                </div> -->
                <div class="float-right">
                  <b-button
                    v-on:click="login" 
                    variant="primary"
                    size="lg"
                    >Login
                  </b-button>
                </div>
              </div>
            </div>
          </div>
          <div class="text-center text-white opacity-8 mt-3">
            Copyright &copy; ArchitectUI 2019
          </div>
        </b-col>
      </div>
    </div>
  </div>
</template>

<script>
import { EventBus } from '@/utils'

export default {
  data(){
    return {
      username: '',
      password: '',
      errorMsg: '',
    }
  },
  methods: {
    login(){
      this.$store.dispatch('login', {
        username: this.username,
        password: this.password
      }).then(()=>{
        this.$router.push('/')
      })
    }
  },
  mounted () {
    EventBus.$on('failedRegistering', (msg) => {
      this.errorMsg = msg
    })
    EventBus.$on('failedAuthentication', (msg) => {
      this.errorMsg = msg
    })
  },
  beforeDestroy () {
    EventBus.$off('failedRegistering')
    EventBus.$off('failedAuthentication')
  }
}
</script>
