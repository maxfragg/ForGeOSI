import virtualbox

class vbox():
	def __init__(self,basename="ubuntu-lts-base",clonename="testvm",mode="clone",linkedName="Forensig20Linked",osType="Linux26",wait=True):
		"""Initialises a virtualbox instance

		The new instance of this class can either reuse an existing virtual machine or create a new one,
		based on a existing template. The concepts of sessions and machines are not exposed to the user"""
		self.vb = virtualbox.Virtualbox()

		if mode=="clone":
			self.vm = self.vb.create_machine("",clonename,[], osType,"")

			_orig = self.vb.find_machine(basename)
			_orig_session = orig.create_session()

			try:
                _snap = _orig.findSnapshot(linkedName)
            except:
            	_orig.lock_machine(_orig_session,virtualbox.library.LockType.shared)

                _snap = _orig_session.console.take_snapshot(linkedName, "")
            	_orig_session.unlock_machine()    

		 	self.progress =  _snap.machine.clone_to(self.vm,virtualbox.library.CloneMode.machine_state, [virtualbox.library.CloneOptions.link])
		 	
		 	if wait:
		 		self.progress.wait_for_completion()

			self.vb.register_machine(self.vm)
		else if mode=="use":
			self.vm = self.vb.find_machine(basename)

		self.session = self.vm.create_session()

	def start(self,type="headless",wait=True):
		self.progress = self.vm.launch_vm_process(self.session, type, '')

		if wait:
			self.progress.wait_for_completion()

	def stop(self):
		self.lock()
		self.session.console.power_down()
		self.unlock()


	def lock(self):
		self.vm.lock_machine(self.session,virtualbox.library.LockType.shared)

	def unlock(self):
		self.session.unlock_machine()