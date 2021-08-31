$(document).ready(function(){

    // $(".model-function").click(function(){
    //     $(".model-function").closest( "ul" ).css( "background-color", "red" );
    // });


    $.ajax({
        url: '/auth/users/get-role-name',
        type: "GET",
        contentType: "application/json; charset=utf-8",
        success: function(response) {

            if(response.roleName == "Secretary"){
                $("#header_Dashboard").hide();
                $("#header_Inventory").hide();
                $("#module_header_admin").hide();
            } else if(response.roleName == "Partner"){
                $("#module_header_admin").hide();
                $("#header_Dashboard").hide();
                $("#header_Inventory").hide();
            } else if(response.roleName == "Marketer"){
                $("#header_Dashboard").hide();
                $("#header_Inventory").hide();
                $("#module_header_admin").hide();
                $("#header_Accounting").hide();
            }
        }
    });
});