module person_feature_compare(
 input previous_valid,current_valid,
 input [23:0] previous_feature,current_feature,
 output color_similar
);
 function integer diff;
 input [7:0] a,b;
 begin if(a>=b)diff=a-b;else diff=b-a;end
 endfunction
 assign color_similar=previous_valid && current_valid
 && previous_feature[23:16]==current_feature[23:16]
 && diff(previous_feature[15:8],current_feature[15:8])<=35
 && diff(previous_feature[7:0],current_feature[7:0])<=35;
endmodule
