$("#tab1").click(function(){
   $(".about").show(1000);
   $(".photos").hide(1000);
   $(this).css("background-color", "#eee");
   $("#tab2").css("background-color", "white");
});
$("#tab2").click(function(){
   $(".photos").show(1000);
   $(".about").hide(1000);
   $(this).css("background-color", "#eee");
   $("#tab1").css("background-color", "white");
});
$(function(){
   $(".photos").hide(1);
   $(".about").hide(1);
});
