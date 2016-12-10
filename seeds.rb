# This file should contain all the record creation needed to seed the database with its default values.
# The data can then be loaded with the rake db:seed (or created alongside the db with db:setup).
#
# Examples:
#
#   cities = City.create([{ name: 'Chicago' }, { name: 'Copenhagen' }])
#   Mayor.create(name: 'Emanuel', city: cities.first)

require 'json'
require 'set'

_create = ActiveSupport::JSON.decode(File.read('db/organization_seeder/CRUD/create.json'))
_update = ActiveSupport::JSON.decode(File.read('db/organization_seeder/CRUD/update.json'))
_delete = ActiveSupport::JSON.decode(File.read('db/organization_seeder/CRUD/delete.json'))


## # HARD RESET DATABASE # #
# _data = ActiveSupport::JSON.decode(File.read('db/organization_seeder/metadata.json'))
# Organization.destroy_all
# Admin.destroy_all
# _data.each do |org, details|
#   organization = Organization.new(
#     :name => org,
#     :classification => details['classification'],
#     :description => details['description']
#   )
#   # create officers
#   details['officers'].each do |email|
#     admin = Admin.new(
#       :email => email,
#     )
#     admin.organizations << organization
#     admin.save
#   end
#   organization.save
# end
## # # # # # # # # # # # # #

#new organization
_create.each do |org, details|

  currOrg = Organization.find_by_name(org)
  
  if not currOrg
    # create organization
    organization = Organization.new(
      :name => org,
      :classification => details['classification'],
      :description => details['description']
    )
    # create officers
    details['officers'].each do |email|
      admin = Admin.new(
        :email => email,
      )
      admin.organizations << organization
      admin.save
    end
    organization.save
  else
    _create.delete(org)
    _update[org] = details
  end
end

_update.each do |org, details|
  
  currOrg = Organization.find_by_name(org)

  if not currOrg # if org doesn't exist, create it
    # create organization
    organization = Organization.new(
      :name => org,
      :classification => details['classification'],
      :description => details['description']
    )
    # create officers
    details['officers'].each do |email|
      admin = Admin.new(:email => email)
      admin.organizations << organization
      admin.save
    end
    organization.save
  else # update only admins
    newAdmins = Set.new(details['officers'])
    oldAdmins = Set.new()
    currOrg.admins.each do |email|
      oldAdmins.add(email)
    end
    xorAdmins = newAdmins ^ oldAdmins

    xorAdmins.each do |email|
      admin = currOrg.admins.where(email: email)[0]
      # deleted admin
      if admin
        id = admin.id
        currOrg.admins.destroy(id)
        Admin.destroy(id)
      else
        admin = Admin.new(:email => email)
        admin.organizations << currOrg
        admin.save
      end
      currOrg.save
    end
  end
end

_delete.each do |org, details|

  currOrg = Organization.find_by_name(org)
  # if org already does not exist
  if currOrg
    #destroy all organization admins
    currOrg.admins.each do |admin| 
      Admin.destroy(admin.id)
    end
    # destroys everything incorporated with it
    Organization.destroy(currOrg.id) 
  end

end


