from bs4 import BeautifulSoup

class Sequence:
	def __init__(self, file):
		self.file = file

		self.init_vars() # load all the vars from the xaml file

	#Initializes all variables for the class file
	def init_vars(self):
		self.xaml = self.read_xaml() # Read xaml file
		self.name = self.get_class_name() # get class name from XAML file
		self.arguments = self.build_arguments(self.get_arguments())
		self.sequences = self.create_sequences(self.get_sequences())

	#Gets the existing XAML
	def get_xaml(self):
		return self.xaml

	#Reads an XAML file
	def read_xaml(self):
		infile = open(self.file, "r")
		data = infile.read()
		infile.close()

		data = data[data.find("<"):len(data)] # remove garbage from start of file
		xaml = BeautifulSoup(data, "xml");
		return xaml

	#Updates a node of the XAML stored in memory
	def update_xaml_node(self, node, new_xaml):
		self.xaml = new_xaml
		self.save()

	#Saves the raw XAML in memory to the XAML file
	def save(self):
		#First we need to strip the <XML> tag that our xaml parser adds
		xml_string = '<?xml version="1.0" encoding="utf-8"?>\n' # The XML encoding tag we need to remove
		data = str(self.xaml).replace(xml_string, "", 1)

		file = open(self.file,"w+")
		file.write(str(data))
		file.close()

		#Re-initialize variables from the newly saved XAML file
		self.init_vars()

		return file

	#Get classname from raw XAML
	def get_class_name(self):
		return self.xaml.find_all("Activity")[0]["x:Class"]

	#Sets a class name for the file
	def set_class_name(self, new_name):
		self.xaml.find("Activity")["x:Class"] = new_name
		self.save()
		return new_name

	#Returns the first sequece/block/whatever in the class. The outmost layer
	def get_first_block(self):
		return self.xaml.find("TextExpression.ReferencesForImplementation").next_sibling.next_sibling

	#Get annotation for node
	def get_annotation(self, node):
		return node["sap2010:Annotation.AnnotationText"]

	#Set annotation for node
	def set_annotation(self, node, text):
		node["sap2010:Annotation.AnnotationText"] = text
		self.save()

	#Gets node name
	def get_node_name(self, node):
		return node["DisplayName"]

	#Sets node name
	def set_node_name(self, node, new_name):
		node["DisplayName"] = new_name
		this.save()
		return new_name

	#Returns an argument by name
	def get_argument_by_name(self, name):
		if not self.arguments is None:
			for item in self.arguments:
				if item.name == name:
					return item

	#Gets arguments of sequence
	def get_arguments(self):
		return self.xaml.find_all("x:Property")

	#Builds the argument objects for the main class
	def build_arguments(self, argument_list):
		if not argument_list is None and len(argument_list) > 0:
			args = []
			for item in argument_list:
				args.append(Sequence.Argument(self, item))
			return args

	#Creates and adds a new argument for the sequence
	def add_argument(self, name, string_direction, datatype):
		new_arg = self.xaml.new_tag("x:Property")
		new_arg["Name"] = name

		#build XAML friendly variables for the passed in arguments
		new_arg_type_end = ")"
		if string_direction == "in":
			new_arg_type_start = "InArgument("
		elif string_direction == "out":
			new_arg_type_start = "OutArgument("
		elif string_direction == "io":
			new_arg_type_start = "InOutArgument("
		else:
			new_arg_type_end = ""
			new_arg_type_start = ""

		#  Type="InArgument(scg:Dictionary(x:String, x:Object))"
		new_arg["Type"] = new_arg_type_start + datatype + new_arg_type_end

		#Add to array in XAML
		self.xaml.find("x:Members").append(new_arg)
		#Rebuild all arguments from the XAML
		self.arguments = self.build_arguments(self.get_arguments())

		self.save()

	#Gets a block by its Displayname
	def get_node_by_display_name(self, display_name):
		return self.xaml.find(DisplayName=display_name)

	#Gets nested sequences
	def get_sequences(self):
		return self.xaml.find_all("Sequence")

	#Builds the argument objects for the main class
	def create_sequences(self, sequence_list):
		if not sequence_list is None and len(sequence_list) > 0:
			sequences = []
			for item in sequence_list:
				sequences.append(Sequence.Inner_Sequence(self, item))
			return sequences


	#To String.
	def __str__(self):
		to_return  = "{" + "\n"
		for key in self.__dict__.keys():
			if key != "xaml":
				if isinstance(self.__dict__[key], (list,)):
					to_return = to_return + "\t" + key + ": [" + "\n"
					for item in self.__dict__[key]:
						to_return = to_return + "\t\t" + str(item) + "\n"
					to_return = to_return + "\t]" + "\n"
				else:
					to_return = to_return + "\t" + key + ":" + str(self.__dict__[key]) + "\n"

		to_return = to_return + "}"
		return to_return

	#-----------------------------------------------------------------------------------------------------------------------
	#  Subclass: Variable
	#  Description: Stores the data about a variable in a sequence
	#-----------------------------------------------------------------------------------------------------------------------
	class Variable():
		def __init__(self, parent=None, xaml = None, name=None, type_arg=None, default=None):
			self.parent = parent #Store the calling sequence

			#If xaml was passed in just use that
			self.xaml = xaml
			if not self.xaml is None:
				self.name = self.xaml["Name"]
				self.type = self.xaml["x:TypeArguments"]
			#Else build new xaml based on the name and type passed in
			else:
				self.name = name
				self.type = type_arg
				self.default = default
				self.xaml = self.build_xaml()

		#Builds XAML for a name and type
		def build_xaml(self):
			new_node = self.parent.xaml.new_tag("Variable") # have the beautiful soup instance from the parent create a new tag
			new_node["Name"] = self.name
			new_node["x:TypeArguments"] = self.type
			if not self.default is None:
				new_node["Default"] = self.default
			return new_node

	#-----------------------------------------------------------------------------------------------------------------------
	#  Subclass: Argument
	#  Description: Stores the arguments and their default values from the xaml file
	#-----------------------------------------------------------------------------------------------------------------------

	#Define subclass for the arguments
	class Argument():
		def __init__(self, outer_sequence, xaml, default_value=None):
			self.outer_sequence = outer_sequence #the containing sequence
			
			self.xaml = xaml
			self.init_vars()
			self.default_value = self.get_default_value_for_attr()
			

		#Creates a new argument

		#Get default value for attribute
		def get_default_value_for_attr(self):
			values_string = self.outer_sequence.xaml.find_all("Activity")[0]
			key = "this:" + self.outer_sequence.name + "." + self.name

			if key in values_string:
				return values_string["this:" + self.outer_sequence.name + "." + self.name]
			
		#Decodes XAML into python friendly strings
		def init_vars(self):
			self.name = self.xaml["Name"]
			self.direction = self.get_direction_from_xaml()
			self.type = self.get_datatype_from_xaml()

		#Converts string direction to xaml direction
		def convert_string_direction_to_xaml(self, string_direction):
			if string_direction == "in":
				return "InArgument"
			elif string_direction == "out":
				return "OutArgument"
			elif string_direction == "io":
				return "InOutArgument"
			else:
				return "Property"

		#Gets direction of argument
		def get_direction_from_xaml(self):
				temp = self.xaml["Type"]

				if "InArgument" in temp:
					return "InArgument"
				elif "OutArgument" in temp:
					return "OutArgument"
				elif "InOutArgument" in temp:
					return "InOutArgument"
				else:
					return "Property"

		#Gets the datatype of the argument
		def get_datatype_from_xaml(self):
			return self.xaml["Type"].replace("(", "").replace(")", "").replace(self.direction, "")

		#Sets a new name value for this Class instance, as well as updating the parent raw XAML.
		def set_name(self, new_name):
			self.update_default_value_name(self.name, new_name)
			self.xaml["Name"] = new_name
			self.name = new_name
			self.update_outer_sequence()
			

		#Sets a new direction value for this Class instance, as well as updating the parent raw XAML.
		def set_direction(self, direction_string):
			self.direction = direction_string #update class' variable

			new_direction_xaml = ""
			if self.direction == "InArgument":
				new_direction_xaml = "InArgument(" + self.type + ")"
			elif self.direction == "InOutArgument":
				self.delete_default_value() #delete default value as it is not supported by this direction type
				new_direction_xaml = "InOutArgument(" + self.type + ")"
			elif self.direction == "OutArgument":
				self.delete_default_value() #delete default value as it is not supported by this direction type
				new_direction_xaml = "OutArgument(" + self.type + ")"
			else:
				new_direction_xaml = self.type

			self.xaml["Type"] = new_direction_xaml
			self.update_outer_sequence()

		#Creates a default value when one does not yet exist
		#STUB

		#Sets a new default value for this Class instance, as well as updating the parent raw XAML.
		def update_default_value(self, new_value):
			self.default_value = new_value
			values_string = self.outer_sequence.xaml.find_all("Activity")[0]
			values_string["this:" + self.outer_sequence.name + "." + self.name] = new_value
			self.update_outer_sequence()

		#Changes the name of default values to match the argument name when it is changed
		def update_default_value_name(self, old_name, new_name):
			values_string = self.outer_sequence.xaml.find_all("Activity")[0]
			key = "this:" + self.outer_sequence.name + "." + self.name
			
			if key in values_string:
				self.delete_default_value()
				values_string["this:" + self.outer_sequence.name + "." + new_name] = self.default_value
				#values_string["this:" + self.outer_sequence.name + "." + self.name] = new_value

		#Deletes the default value
		def delete_default_value(self):
			values_string = self.outer_sequence.xaml.find_all("Activity")[0]
			key = "this:" + self.outer_sequence.name + "." + self.name
			
			if key in values_string:
				del self.outer_sequence.xaml.find_all("Activity")[0]["this:" + self.outer_sequence.name + "." + self.name]

			if not self.default_value is None:
				del self.default_value

		#Update parent Sequence XAML. Do this when using any setter method defined above
		def update_outer_sequence(self):
			#if not self.outer_sequence.xaml.find(attrs={"Name":self.name})["Name"] is None:
			self.outer_sequence.xaml.find(attrs={"Name":self.name}).replace_with(self.xaml)
			self.outer_sequence.save()

		#override to string method
		def __str__(self):
			if self.default_value is None: # check if self has default_value
				return "{name: \"" + self.name + "\", direction: \"" + self.direction + "\", type: \"" + self.type + "\"}"
			else:
				return "{name: \"" + self.name + "\", direction: \"" + self.direction + "\", type: \"" + self.type + "\", default_value: \"" + self.default_value + "\"}"


	#-----------------------------------------------------------------------------------------------------------------------
	#  Subclass: Argument
	#  Description: Stores the arguments and their default values from the xaml file
	#-----------------------------------------------------------------------------------------------------------------------

	#Define subclass for the arguments
	class Inner_Sequence():
		def __init__(self, outer_sequence, xaml):
			self.outer_sequence = outer_sequence
			self.xaml = xaml
			self.id = xaml["sap2010:WorkflowViewState.IdRef"]
			self.get_invoked_workflow()
			self.variables = self.get_sequence_variables()

		#Get the invoked workflow for the sequences, if applicable
		def get_invoked_workflow(self):
			self.invoked_workflow = self.xaml.find("ui:InvokeWorkflowFile")

			if not self.invoked_workflow is None:
				#Get path to invoked workflow
				self.invoked_workflow_path = self.invoked_workflow["WorkflowFileName"]
				
				#get arguments of invoked workflow
				self.invoked_workflow_arguments_xaml = self.invoked_workflow.find("ui:InvokeWorkflowFile.Arguments")
				
				if len(self.invoked_workflow_arguments_xaml.findChildren()) > 0:
					self.invoked_workflow_arguments = []
					for index,child in enumerate(self.invoked_workflow_arguments_xaml.findChildren()):
						self.invoked_workflow_arguments.append(Sequence.Inner_Sequence.Invoked_Workflow_Argument(self, child, index))

		#Get variables in this sequence
		def get_sequence_variables(self):
			vars_from_xaml = self.xaml.find_all("Variable")
			
			#If there are any variables, we will build an array of variable objects and return them
			if len(vars_from_xaml) > 0:
				all_vars = []

				for item in self.xaml.find_all("Variable"):
					all_vars.append(self.outer_sequence.Variable(self.outer_sequence, xaml=item))

				return all_vars

		#Add variable to sequence
		def create_variable(self, xaml=None, name=None, type=None, default=None):
			#If xaml is None, build new BS node
			if xaml is None:
				xaml = self.outer_sequence.xaml.new_tag("Variable")
				xaml["Name"] = name
				xaml["x:TypeArguments"] = type

				if not default is None:
					xaml["Default"] = default

			self.xaml.find("Sequence.Variables").append(xaml) #Add new variable to xaml file
			self.variables = self.get_sequence_variables() #Regenerate vars from xaml
			self.update_outer_sequence()

			return xaml #return the new variable

		#Deletes a variable by name
		def delete_variable(self, var_name):
			self.xaml.find_all("Variable", Name=var_name)[0].decompose() #Deletes the variable from the XAML
			self.variables = self.get_sequence_variables() #Regenerate vars from xaml
			self.update_outer_sequence()


		#Imports arguments from invoked function. Just like the button in UiPath
		def import_arguments(self):
			#Clear the array of invoked workflow argument objects
			self.invoked_workflow_arguments = []
			self.invoked_workflow_arguments_xaml.clear()
			#clear the array of 
			invoked_sequence = Sequence(self.invoked_workflow_path) #Load the invoked sequence

			#Create new nodes for each of the imported arguments
			for index,item in enumerate(invoked_sequence.arguments):
				#Determine new node type
				new_node_type = item.direction

				#build a new Invoked_Workflow_Argument object
				new_node = self.outer_sequence.xaml.new_tag(new_node_type) # have the beautiful soup instance from the parent create a new tag
				new_node["x:Key"] = item.name
				new_node["x:TypeArguments"] = item.type
				new_node.string = "" #Add this so BS adds a closing tag

				#Add it to this sequence's invoked workflow arguments
				self.invoked_workflow_arguments.append(Sequence.Inner_Sequence.Invoked_Workflow_Argument(self, new_node, index))
				#Add new node to the invoked_arguments_xaml
				self.invoked_workflow_arguments_xaml.append(new_node)

			self.update_outer_sequence()
			return self.invoked_workflow_arguments

		#Update parent Sequence XAML. Do this when using any setter method defined above
		def update_outer_sequence(self):
			#if not self.outer_sequence.xaml.find(attrs={"Name":self.name})["Name"] is None:
			self.outer_sequence.xaml.find(attrs={"sap2010:WorkflowViewState.IdRef":self.id}).replace_with(self.xaml)
			self.outer_sequence.save()

		#To String
		def __str__(self):
			return str(self.xaml.prettify())

		#Define inner class for invoked_argument
		class Invoked_Workflow_Argument():
			def __init__(self, parent, xaml, index):
				self.parent = parent
				self.xaml = xaml
				self.name = xaml.name
				self.index = index
				self.key = self.xaml["x:Key"]
				self.type = self.xaml["x:TypeArguments"]
				self.value = self.xaml.getText()
				self.value_type = "value" # if the value is a pre-entered value and not a variable

				#Check if the value is a variable (denoted by square braces)
				if "[" in self.value:
					self.value = self.value[1:(len(self.value) - 1)]
					self.value_type = "variable"

			#Change the value of the argument (passing a value, not a variable)
			def set_value(self, new_value):
				self.value = new_value
				self.value_type = "value"
				self.xaml.string = new_value
				self.update_parent()

			#Change the value of the argument (the variable that is entered)
			def set_value_to_variable(self, variable):
				self.value = variable
				self.value_type = "variable"
				self.xaml.string = "[" + variable + "]"
				self.update_parent()

			#Change the key that the argument is pointing to
			def set_key(self, new_value):
				self.key = new_value
				self.xaml["x:Key"] = new_value
				self.update_parent()

			#Change the data type of the argument
			def set_type(self, new_type):
				if new_type == "InArgument":
					self.name = "InArgument"
					self.xaml.name = "InArgument"
				elif new_type == "OutArgument":
					self.name = "OutArgument"
					self.xaml.name = "OutArgument"
				elif new_type == "InOutArgument":
					self.name = "InOutArgument"
					self.xaml.name = "InOutArgument"
				self.update_parent()



			#Update parent Sequence XAML. Do this when using any setter method defined above
			def update_parent(self):
				self.parent.invoked_workflow.find("ui:InvokeWorkflowFile.Arguments").findChildren()[self.index].replace_with(self.xaml)
				self.parent.update_outer_sequence()

