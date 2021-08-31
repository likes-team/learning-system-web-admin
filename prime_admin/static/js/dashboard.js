$(document).ready(function(){
    var ctx_chart_sales = document.getElementById('chart_sales');
    ctx_chart_sales.height = 150;

    var maintaining_sales_data;
    var gross_sales_data;
    var expenses_data;

    $(".btn-branch").click(function(){
        $('.active').removeClass('active');
        $(this).addClass('active');

        var branch_id = $(this).val();
        
        $.ajax({
            url: '/learning-management/api/dashboard/get-chart-data/' + branch_id,
            type: "GET",
            contentType: "application/json; charset=utf-8",
            success: function(response) {
                maintaining_sales_data = response.maintaining_sales;
                gross_sales_data = response.gross_sales;
                expenses_data = response.expenses;
                net_data = response.net;

                $("#tbl_dashboard > tbody").empty();
                
                $('#tbl_dashboard > tbody:first').append(
                    `<tr>
                    <th scope="row">GROSS SALES</th>
                    <td>${response.gross_sales[0] || ""}</td>
                    <td>${response.gross_sales[1] || ""}</td>
                    <td>${response.gross_sales[2] || ""}</td>
                    <td>${response.gross_sales[3] || ""}</td>
                    <td>${response.gross_sales[4] || ""}</td>
                    <td>${response.gross_sales[5] || ""}</td>
                    <td>${response.gross_sales[6] || ""}</td>
                    <td>${response.gross_sales[7] || ""}</td>
                    <td>${response.gross_sales[8] || ""}</td>
                    <td>${response.gross_sales[9] || ""}</td>
                    <td>${response.gross_sales[10] || ""}</td>
                    <td>${response.gross_sales[11] || ""}</td>
                    </tr>`
                    );
    
                 $('#tbl_dashboard > tbody:first').append(
                    `<tr>
                    <th scope="row">EXPENSES</th>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                    </tr>`
                    );
                    
                $('#tbl_dashboard > tbody:first').append(
                    `<tr>
                    <th scope="row">NET</th>
                    <td>${net_data[0] || ""}</td>
                    <td>${net_data[1] || ""}</td>
                    <td>${net_data[2] || ""}</td>
                    <td>${net_data[3] || ""}</td>
                    <td>${net_data[4] || ""}</td>
                    <td>${net_data[5] || ""}</td>
                    <td>${net_data[6] || ""}</td>
                    <td>${net_data[7] || ""}</td>
                    <td>${net_data[8] || ""}</td>
                    <td>${net_data[9] || ""}</td>
                    <td>${net_data[10] || ""}</td>
                    <td>${net_data[11] || ""}</td>
                    </tr>`
                    );
    
                    $('#tbl_dashboard > tbody:first').append(
                        `<tr>
                        <th scope="row">MAINTAINING SALE 85K</th>
                        <td>${response.maintaining_sales[0] || ""}</td>
                        <td>${response.maintaining_sales[1] || ""}</td>
                        <td>${response.maintaining_sales[2] || ""}</td>
                        <td>${response.maintaining_sales[3] || ""}</td>
                        <td>${response.maintaining_sales[4] || ""}</td>
                        <td>${response.maintaining_sales[5] || ""}</td>
                        <td>${response.maintaining_sales[6] || ""}</td>
                        <td>${response.maintaining_sales[7] || ""}</td>
                        <td>${response.maintaining_sales[8] || ""}</td>
                        <td>${response.maintaining_sales[9] || ""}</td>
                        <td>${response.maintaining_sales[10] || ""}</td>
                        <td>${response.maintaining_sales[11] || ""}</td>
                        </tr>`
                        );    
    
                    $('#tbl_dashboard > tbody:first').append(
                        `<tr>
                        <th scope="row">NO. OF STUDENTS</th>
                        <td>${response.no_of_students[0] || ""}</td>
                        <td>${response.no_of_students[1] || ""}</td>
                        <td>${response.no_of_students[2] || ""}</td>
                        <td>${response.no_of_students[3] || ""}</td>
                        <td>${response.no_of_students[4] || ""}</td>
                        <td>${response.no_of_students[5] || ""}</td>
                        <td>${response.no_of_students[6] || ""}</td>
                        <td>${response.no_of_students[7] || ""}</td>
                        <td>${response.no_of_students[8] || ""}</td>
                        <td>${response.no_of_students[9] || ""}</td>
                        <td>${response.no_of_students[10] || ""}</td>
                        <td>${response.no_of_students[11] || ""}</td>
                        </tr>`
                        );        
                
                
                const labels = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                const data = {
                labels: labels,
                datasets: [
                    {
                    label: 'Gross Sales',
                    data: gross_sales_data,
                    borderColor: 'rgba(0, 120, 246, 1)',
                    backgroundColor: 'rgba(0, 120, 246, 0.5)',
                    fill: false,
    
                    },
                    {
                    label: 'Expenses',
                    data: expenses_data,
                    borderColor: 'rgba(247, 255, 0, 1)',
                    backgroundColor: 'rgba(247, 255, 0, 0.5)',
                    fill: false,
                    },
                    {
                        label: 'NET',
                        data: net_data,
                        borderColor: 'rgba(251, 145, 79, 1)',
                        backgroundColor: 'rgba(251, 145, 79, 0.5)',
                        fill: false,
                    },
                    {
                        label: 'Maintaining Sales',
                        data: maintaining_sales_data,
                        borderColor: 'rgba(255, 0, 0, 1)',
                        backgroundColor: 'rgba(255, 0, 0, 0.5)',
                        fill: false,
                    }
                ]
                };
    
                const config = {
                type: 'line',
                data: data,
                options: {
                    responsive: true,
                    plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: true,
                        text: 'Chart.js Line Chart'
                    }
                    }
                },
                };
    
                var chart_sales = new Chart(ctx_chart_sales, config);
    
            }
        });

    });
});