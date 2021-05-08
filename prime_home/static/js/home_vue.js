    const home = new Vue({
    el: '#home',
    data: {
        
    },
    methods: {
        scrollGoToAbout() {
            const element = document.getElementById('about');
            element.scrollIntoView({ behavior: 'smooth' });
        },

        srcollGotoTestimonies(){
            const element = document.getElementById('testimonies');
            element.scrollIntoView({ behavior: 'smooth' });
        }
    }
})