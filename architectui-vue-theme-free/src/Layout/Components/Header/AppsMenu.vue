<template>
    <ul class="header-menu nav">
        <li v-for="module in modules" :key="module.name" class="nav-item">
            <button v-on:click="changeCurrentModule(module)" class="btn btn-link">
                <i class="nav-link-icon pe-7s-home"> </i>
                {{module.short_description}}
            </button>
        </li>
    </ul>
</template>

<script>
    export default {
        data() {
            return {
                // modules: [],
            }
        },
        computed: {
            modules() {
                return this.$store.getters.getAppMenuModules;
            }
        },
        methods: {
            changeCurrentModule(module){
                this.$store.dispatch('changeCurrentModule', module);
            }
        }
    }
</script>