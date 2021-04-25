$(document).ready(function(){

    $("#div_marketer_buttons").on('click', '.btn-marketer', function () {
        var marketer_name = $(this).html();

        // if(!(localStorage.getItem('sessSubArea') == _sub_area_name)){
        $("#btn_marketer_label").html(marketer_name.toUpperCase());
        $("#btn_marketer_label").val($(this).val());
        $("#card_header_label").html(marketer_name);
        // dtbl_subscribers.ajax.url(`/bds/api/sub-areas/${$(this).val()}/subscribers`).load();
        // }

    });
});