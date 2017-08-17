(function($){
  $(function(){

    $('.button-collapse').sideNav();
    // $('.parallax').parallax();

  }); // end of document ready
})(jQuery); // end of jQuery name space

  var work_hours = function (s,e) {
    var i = 0;
    var idx = 0;
    var data = [];
    for (s; s <= e; s.setDate(s.getDate() + 1)) {
      console.log(s);
      var dato = s.toDateString();       
      // i = i +1;
      var day = s.getDay();
      var isWeekend = (day == 6) || (day == 0);
      // console.log(isWeekend);
      if(!isWeekend) {
        i = i + 8;
        data.push(dato);
      } 
    }
    return [i,data];
  }

  $( document ).ready(function() {

    $(".burger").on("click", function  () {

      $("#index-banner").toggleClass("index-bannerTop");
      $("#nav-mobile").toggleClass("show");
      $("#nav-mobile").toggle();
    });
  
  var select_start_date;
  var start_date = $('#start_date').pickadate({
    selectMonths: true, // Creates a dropdown to control month
    selectYears: 3, // Creates a dropdown of 15 years to control year,
    today: 'Hoy',
    clear: 'Limpiar',
    close: 'Ok',
    firstDay: 1,
    format: 'dd-mm-yyyy',
    formatSubmit: 'yyyy-mm-dd',
    closeOnSelect: true, // Close upon selecting a date,
    monthsFull: ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'],
    monthsShort: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'],
    weekdaysFull: ['Domingo', 'Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado'],
    weekdaysShort: ['Dom', 'Lun', 'Mar', 'Mie', 'Jue', 'Vie', 'Sab'],
    showMonthsShort: true,
    hiddenName: true,
    onClose: function() {
      // console.log(start_date)
      var a = [];
      var s = start_date.pickadate('picker');
      select_start_date = s.get('select', 'yyyy-mm-dd');
      a = select_start_date.toString().split("-");
      var integers = a.map(function(x) {
        return parseInt(x,10);
      });
      integers[1] = integers[1] - 1; // los meses estan en base 0
      var e = end_date.pickadate('picker');
      e.set( 'min',integers);
    },

  });

  var end_date = $('#end_date').pickadate({
    selectMonths: true, // Creates a dropdown to control month
    selectYears: 3, // Creates a dropdown of 15 years to control year,
    today: 'Hoy',
    clear: 'Limpiar',
    close: 'Ok',
    firstDay: 1,
    format: 'dd-mm-yyyy',
    formatSubmit: 'yyyy-mm-dd',
    closeOnSelect: true, // Close upon selecting a date,
    monthsFull: ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'],
    monthsShort: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'],
    weekdaysFull: ['Domingo', 'Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado'],
    weekdaysShort: ['Dom', 'Lun', 'Mar', 'Mie', 'Jue', 'Vie', 'Sab'],
    showMonthsShort: true,
    hiddenName: true,
    onClose: function() {
      var e = end_date.pickadate('picker');
      select_end_date = e.get('select', 'yyyy-mm-dd');
      var startDate = new Date(select_start_date);
      var endDate = new Date(select_end_date);
      // console.log(endDate - startDate);
      work_days = work_hours(startDate,endDate);
      wh = work_days[0]
      wd = work_days[1]
      console.log(work_days);
      $('#hours').val(wh);
    }
  });  
  $('#check_all[type="checkbox"]+label').on('click', function(){
    if(!$("#check_all").prop('checked')){
      $("#check_all").prop('checked', true);
      $(".checkBoxClass").prop('checked', true);
    }else{
      $("#check_all").prop('checked', false);
      $(".checkBoxClass").prop('checked', false);
    }
  });


    $('select').material_select();
  //   $(document).on('change', '#project', function() {
  // // Does some stuff and logs the event to the console
  //     console.log($(this));
  //   });
  //   $('select[name=project]').change(function() { console.log($(this).attr('data')); });
  $('select[name=project]').on('change', function(e){ 
    var data = $(this).find("option:selected").data('id');
    console.log( data ); 
    var opts = data.split(',');
    console.log(opts);
      $('select[name=approver]').material_select('destroy');

    for(var i =0;i < opts.length; i++){
      // $('select[name=approver]').append('<option value="'+opts[i]+'">'+opts[i]+'</option>');
      $('#approver').append('<option value="'+opts[i]+'">'+opts[i]+'</option>');
      console.log(opts[i]);
    }
    e.preventDefault(); 
    $('select[name=approver]').material_select();
  }); 

});

