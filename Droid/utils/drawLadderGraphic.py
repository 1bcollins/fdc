'''
ladder_structure = [0, 1, 2, 3]

droid['tickBuckets']

if (droid['tickBuckets']==3):
"graphic horizontal"

   xxx
  xxx
 xxx
xxx

   ███        <-- ladder_structure[3]
  ███           <-- ladder_structure[2]
 ███              <-- ladder_structure[1]
███                <-- ladder_structure[0]
   ▲               <-- price lives here
   
   
for a 
ladder_structure = [0, -1, -2, -3]

droid['tickBuckets']

if (droid['tickBuckets']==3):
"grapic"
  ███        <-- ladder_structure[3]
   ███           <-- ladder_structure[2]
    ███              <-- ladder_structure[1]
     ███                <-- ladder_structure[0]
   ▲               <-- price lives here
'''

def draw_staggered_ladder(ladder_structure, tick_buckets, current_tick, tick_spacing, centerPosTickLower, offSet):	#, centerPosTickUpper)  :
	
	BLUE = "\033[34m"
	GREEN = "\033[32m"
	RED = "\033[31m"
	RESET = "\033[0m"
		
	
	#block = "███"
	blockUnit="███"	#"█"
	block = ""
	i=-1
	for bucket in range(tick_buckets):
		i=i+1
		color=BLUE if (i % 2)==0 else GREEN	#: "flip color"
		block=block + color + blockUnit
	
	#print("block: ", block)
	
	#block_width = len(block)
	space_unit = " " * len(blockUnit) ##* block_width  # unit of horizontal offset
	
	
	zeroIndex=int(centerPosTickLower/tick_spacing)
	currentTickIndex=int(current_tick/tick_spacing)
	currTickRelativeIndex=currentTickIndex-zeroIndex-1
	print("currTickRelativeIndex: ", currTickRelativeIndex)
	
	#find most negative index
	minValue=min(ladder_structure)
	margin=4
	center=margin+abs(minValue)
	
	# Render ladder (top to bottom)
	print("\n📊 Ladder Structure:\n")
	for i in reversed(range(len(ladder_structure))):
		indent_count = abs(ladder_structure[i]) if i<0 else (center+ladder_structure[i])
		indent_count= indent_count*offSet
		indent = space_unit * abs(indent_count)
		'''
		color=BLUE if (i % 2)==0 else RESET	#: "flip color"
		row = f"{color}{indent}{block}"
		'''
		row = f"{indent}{block}"
		print(row)

	#if price_index is not None:
	#arrow_indent = space_unit * (len(blockUnit)*currTickRelativeIndex + margin + 1)	#abs(price_index if is_descending else ladder_structure[price_index])
	arrow_indent = space_unit * (center*offSet + currTickRelativeIndex)
	print(f"{RESET}{arrow_indent} ▲  ← current price in this bucket\n")


# ---------- EXECUTE ---------- #
if __name__ == "__main__":
	ladder_structure=[0,1,-2,-3]
	tick_spacing=60
	current_tick=-197970	#-198030	#-197970	#-197773
	tick_buckets=3
	centerPosTickLower = -198060
	centerPosTickUpper = -197880
	offSet=1
	draw_staggered_ladder(ladder_structure, tick_buckets, current_tick, tick_spacing, centerPosTickLower, offSet)	#, centerPosTickUpper)  
	
	
	
	
	
	
	
	
