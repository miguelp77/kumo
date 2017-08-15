(function($){
  $(function(){

    $('.button-collapse').sideNav();
    // $('.parallax').parallax();

  }); // end of document ready
})(jQuery); // end of jQuery name space

  $( document ).ready(function() {

    $(".burger").on("click", function  () {

      $("#index-banner").toggleClass("index-bannerTop");
      $("#nav-mobile").toggleClass("show");
      $("#nav-mobile").toggle();
    });
  });