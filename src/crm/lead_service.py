from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.shared.crm_models import Lead, LeadActivity, LeadAssignment, Employee, WebsiteLead, SocialMediaLead, Disbursement, LeadComment

class LeadService:
    """Service for managing unified lead workflow and activity logging"""
    
    # Enhanced Lead status flow with proper progression based on actual database
    LEAD_STATUSES = {
        'new': 'New Lead',
        'assigned': 'Assigned',
        'qualified': 'Qualified',
        'pd': 'PD (Personal Discussion)',
        'documentation': 'Documentation',
        'login': 'Login',
        'underwriter': 'Underwriter',
        'approved': 'Approved',
        'rejected': 'Rejected',
        'disbursed': 'Disbursed',
        'closed': 'Closed'
    }
    
    # Enhanced Status transitions with undo capability based on actual workflow
    STATUS_FLOW = {
        'new': ['assigned'],
        'assigned': ['qualified', 'closed'],
        'qualified': ['pd', 'assigned', 'closed'],
        'pd': ['documentation', 'qualified', 'closed'],
        'documentation': ['login', 'pd', 'closed'],
        'login': ['underwriter', 'documentation', 'closed'],
        'underwriter': ['approved', 'rejected', 'login', 'closed'],
        'approved': ['disbursed', 'underwriter', 'closed'],
        'rejected': ['underwriter', 'closed'],
        'disbursed': ['closed'],
        'closed': []
    }
    
    # Close type mapping for different closure reasons
    CLOSE_TYPES = {
        'approved': 'Approved & Closed',
        'rejected': 'Rejected & Closed', 
        'not_doable': 'Not Doable',
        'cancelled': 'Cancelled by Customer',
        'duplicate': 'Duplicate Lead'
    }
    
    # Status descriptions for UI
    STATUS_DESCRIPTIONS = {
        'new': 'Lead has been created and is awaiting assignment',
        'assigned': 'Lead has been assigned to an employee',
        'qualified': 'Lead has been qualified and is ready for processing',
        'pd': 'Personal Discussion completed, collecting documents',
        'documentation': 'Documentation is being processed',
        'login': 'Application has been logged into the system',
        'login_query': 'Login query is being processed',  # Legacy status support
        'underwriter': 'Case is under review by underwriter',
        'approved': 'Loan has been approved',
        'rejected': 'Loan has been rejected',
        'disbursed': 'Loan amount has been disbursed',
        'closed': 'Case has been closed'
    }
    
    @staticmethod
    def get_next_possible_statuses(current_status: str) -> List[str]:
        """Get possible next statuses for the current status"""
        return LeadService.STATUS_FLOW.get(current_status, [])
    
    @staticmethod
    def get_previous_possible_statuses(current_status: str) -> List[str]:
        """Get possible previous statuses (for undo functionality)"""
        previous_statuses = []
        for status, next_statuses in LeadService.STATUS_FLOW.items():
            if current_status in next_statuses:
                previous_statuses.append(status)
        return previous_statuses
    
    @staticmethod
    def can_update_lead_info(user_role: str, assignment: LeadAssignment = None) -> bool:
        """Check if user can update lead information"""
        return user_role in ['admin', 'manager'] or (assignment and assignment.employee_id)
    
    @staticmethod
    def can_delete_comment(user_role: str, comment_employee_id: int, current_employee_id: int) -> bool:
        """Check if user can delete a comment"""
        return user_role in ['admin', 'manager'] or comment_employee_id == current_employee_id
    
    @staticmethod
    def create_lead_from_website(db: Session, name: str, contact: str, email: str, message: str) -> Lead:
        """Create a unified lead from website form"""
        lead = Lead(
            source='website',
            name=name,
            contact=contact,
            email=email,
            message=message,
            status='new',
            additional_data={'original_message': message}
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)
        
        # Log activity
        LeadService.log_activity(
            db=db,
            lead_id=lead.lead_id,
            activity_type='created',
            description=f'Lead created from website contact form',
            activity_data={'source': 'website', 'form_type': 'contact'}
        )
        
        return lead
    
    @staticmethod
    def create_lead_from_social(db: Session, name: str, contact: str, city: str, 
                               loan_amount: float, platform: str, ongoing_loan: str = None) -> Lead:
        """Create a unified lead from social media"""
        lead = Lead(
            source='social',
            name=name,
            contact=contact,
            city=city,
            loan_amount=loan_amount,
            platform_name=platform,
            any_ongoing_loan=ongoing_loan,
            status='new',
            additional_data={'platform': platform, 'ongoing_loan': ongoing_loan}
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)
        
        # Log activity
        LeadService.log_activity(
            db=db,
            lead_id=lead.lead_id,
            activity_type='created',
            description=f'Lead created from {platform}',
            activity_data={'source': 'social', 'platform': platform}
        )
        
        return lead
    
    @staticmethod
    def create_manual_lead(db: Session, name: str, contact: str, email: str = None,
                          city: str = None, date_of_birth: str = None, loan_amount: float = None, loan_type: str = None,
                          occupation: str = None, ongoing_loan: str = None, message: str = None,
                          created_by_employee_id: int = None) -> Lead:
        """Create a manual lead entry"""
        # Prepare additional data
        additional_data = {'created_by_employee_id': created_by_employee_id}
        if date_of_birth:
            additional_data['date_of_birth'] = date_of_birth
            
        lead = Lead(
            source='manual',
            name=name,
            contact=contact,
            email=email,
            city=city,
            loan_amount=loan_amount,
            loan_type=loan_type,
            occupation=occupation,
            any_ongoing_loan=ongoing_loan,
            message=message,
            status='new',
            additional_data=additional_data
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)
        
        # Log activity
        LeadService.log_activity(
            db=db,
            lead_id=lead.lead_id,
            employee_id=created_by_employee_id,
            activity_type='created',
            description=f'Manual lead created',
            activity_data={'source': 'manual', 'created_by': created_by_employee_id}
        )
        
        return lead
    
    @staticmethod
    def assign_lead(db: Session, lead_id: int, employee_id: int, assigned_by: int, notes: str = None) -> LeadAssignment:
        """Assign a lead to an employee"""
        # Check if lead is already assigned
        existing_assignment = db.query(LeadAssignment).filter(LeadAssignment.lead_id == lead_id).first()
        if existing_assignment:
            raise ValueError("Lead is already assigned")
        
        # Create assignment
        assignment = LeadAssignment(
            lead_id=lead_id,
            employee_id=employee_id,
            assigned_by=assigned_by,
            notes=notes,
            status='assigned'
        )
        db.add(assignment)
        
        # Update lead status
        lead = db.query(Lead).filter(Lead.lead_id == lead_id).first()
        if lead:
            lead.status = 'assigned'
        
        db.commit()
        db.refresh(assignment)
        
        # Log activity
        LeadService.log_activity(
            db=db,
            lead_id=lead_id,
            employee_id=assigned_by,
            activity_type='assigned',
            description=f'Lead assigned to employee',
            activity_data={'assigned_to': employee_id, 'notes': notes}
        )
        
        return assignment
    
    @staticmethod
    def update_lead_status(db: Session, assignment_id: int, new_status: str, employee_id: int, 
                          comment: str = None, undo_old_status: str = None, close_type: str = None) -> bool:
        """Update lead status with undo capability and close type tracking"""
        assignment = db.query(LeadAssignment).filter(LeadAssignment.assignment_id == assignment_id).first()
        if not assignment:
            return False
        
        # Validate status transition
        if undo_old_status:
            # This is an undo operation
            if new_status not in LeadService.get_previous_possible_statuses(undo_old_status):
                return False
        else:
            # This is a forward operation
            if new_status not in LeadService.get_next_possible_statuses(assignment.status):
                return False
        
        current_status = assignment.status
        assignment.status = new_status
        assignment.last_updated = datetime.now()
        
        # Set close_type when closing leads and update doable status
        if new_status == 'closed':
            if close_type and close_type in LeadService.CLOSE_TYPES:
                assignment.close_type = close_type
            elif current_status == 'approved':
                assignment.close_type = 'approved'
            elif current_status == 'rejected':
                assignment.close_type = 'rejected'
            elif current_status in ['new', 'assigned', 'pd', 'documentation', 'login']:
                assignment.close_type = 'not_doable'
            else:
                assignment.close_type = 'not_doable'  # Default fallback
            
            # When closing, set doable to False (not doable)
            assignment.is_doable = False
            
        # When rejecting, also set doable to False (not doable)
        elif new_status == 'rejected':
            assignment.is_doable = False
        
        # Update lead status
        lead = db.query(Lead).filter(Lead.lead_id == assignment.lead_id).first()
        if lead:
            lead.status = new_status
            if new_status == 'closed':
                lead.state = 'closed'
        
        db.commit()
        
        # Log activity
        activity_type = 'status_undone' if undo_old_status else 'status_changed'
        activity_data = {
            'old_status': current_status, 
            'new_status': new_status, 
            'comment': comment
        }
        if new_status == 'closed' and assignment.close_type:
            activity_data['close_type'] = assignment.close_type
        
        # Add doable status change to activity data if it was changed
        if new_status in ['rejected', 'closed']:
            activity_data['doable_status_changed'] = 'Set to Not Doable'
            
        description = f'Status changed from {current_status} to {new_status}'
        if new_status == 'closed' and assignment.close_type:
            description += f' (Closed: {LeadService.CLOSE_TYPES.get(assignment.close_type, assignment.close_type)})'
        if new_status in ['rejected', 'closed']:
            description += ' - Marked as Not Doable'
            
        LeadService.log_activity(
            db=db,
            lead_id=assignment.lead_id,
            employee_id=employee_id,
            activity_type=activity_type,
            description=description,
            activity_data=activity_data
        )
        
        # Add comment if provided
        if comment:
            LeadService.add_comment(db, assignment.lead_id, employee_id, comment)
        
        return True
    
    @staticmethod
    def add_comment(db: Session, lead_id: int, employee_id: int, comment: str) -> LeadComment:
        """Add a comment to a lead"""
        try:
            # Get the assignment for this lead
            assignment = db.query(LeadAssignment).filter(LeadAssignment.lead_id == lead_id).first()
            if not assignment:
                raise ValueError(f"No assignment found for lead {lead_id}")
            
            lead_comment = LeadComment(
                assignment_id=assignment.assignment_id,
                employee_id=employee_id,
                comment=comment
            )
            
            db.add(lead_comment)
            db.commit()
            db.refresh(lead_comment)
            
            # Log activity
            LeadService.log_activity(
                db=db,
                lead_id=lead_id,
                employee_id=employee_id,
                activity_type='comment_added',
                description=f'Comment added: {comment[:50]}{"..." if len(comment) > 50 else ""}',
                activity_data={'comment': comment}
            )
            
            return lead_comment
        except Exception as e:
            raise
    
    @staticmethod
    def delete_comment(db: Session, comment_id: int, employee_id: int, user_role: str) -> bool:
        """Delete a comment with permission check"""
        comment = db.query(LeadComment).filter(LeadComment.comment_id == comment_id).first()
        if not comment:
            return False
        
        # Check permissions
        if not LeadService.can_delete_comment(user_role, comment.employee_id, employee_id):
            return False
        
        # Log activity before deletion
        LeadService.log_activity(
            db=db,
            lead_id=comment.lead_id,
            employee_id=employee_id,
            activity_type='comment_deleted',
            description=f'Comment deleted: {comment.comment[:50]}{"..." if len(comment.comment) > 50 else ""}',
            activity_data={'deleted_comment': comment.comment}
        )
        
        db.delete(comment)
        db.commit()
        return True
    
    @staticmethod
    def update_lead_info(db: Session, lead_id: int, employee_id: int, user_role: str, 
                        **kwargs) -> bool:
        """Update lead information with permission check"""
        lead = db.query(Lead).filter(Lead.lead_id == lead_id).first()
        if not lead:
            return False
        
        # Check if user can update this lead
        assignment = db.query(LeadAssignment).filter(LeadAssignment.lead_id == lead_id).first()
        if not LeadService.can_update_lead_info(user_role, assignment):
            return False
        
        # Track changes
        changes = {}
        for key, value in kwargs.items():
            if hasattr(lead, key) and getattr(lead, key) != value:
                changes[key] = {'old': getattr(lead, key), 'new': value}
                setattr(lead, key, value)
        
        if changes:
            lead.updated_at = datetime.now()
            db.commit()
            
            # Log activity
            LeadService.log_activity(
                db=db,
                lead_id=lead_id,
                employee_id=employee_id,
                activity_type='lead_updated',
                description=f'Lead information updated',
                activity_data={'changes': changes}
            )
        
        return True
    
    @staticmethod
    def log_activity(db: Session, lead_id: int, activity_type: str, description: str,
                    activity_data: Dict[str, Any] = None, employee_id: int = None) -> LeadActivity:
        """Log an activity for a lead"""
        activity = LeadActivity(
            lead_id=lead_id,
            employee_id=employee_id,
            activity_type=activity_type,
            description=description,
            activity_data=activity_data or {}
        )
        db.add(activity)
        db.commit()
        db.refresh(activity)
        return activity
    
    @staticmethod
    def bulk_import_leads(db: Session, csv_content: str, created_by_employee_id: int, skip_duplicates: bool = True) -> Dict[str, Any]:
        """Bulk import leads from CSV content"""
        import csv
        import io
        from datetime import datetime
        
        success_count = 0
        skipped_count = 0
        error_count = 0
        errors = []
        
        try:
            # Parse CSV content
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            
            for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 because header is row 1
                try:
                    # Validate required fields
                    if not row.get('name') or not row.get('contact'):
                        errors.append(f"Row {row_num}: Name and contact are required")
                        error_count += 1
                        continue
                    
                    # Check for duplicates if skip_duplicates is True
                    if skip_duplicates:
                        existing_lead = db.query(Lead).filter(
                            Lead.contact == row['contact'].strip()
                        ).first()
                        if existing_lead:
                            skipped_count += 1
                            continue
                    
                    # Prepare additional data
                    additional_data = {'created_by_employee_id': created_by_employee_id}
                    if row.get('date_of_birth'):
                        additional_data['date_of_birth'] = row['date_of_birth']
                    
                    # Create lead
                    lead = Lead(
                        source='manual',  # All bulk imported leads are tagged as manual
                        name=row['name'].strip(),
                        contact=row['contact'].strip(),
                        email=row.get('email', '').strip() if row.get('email') else None,
                        city=row.get('city', '').strip() if row.get('city') else None,
                        loan_amount=float(row['loan_amount']) if row.get('loan_amount') and row['loan_amount'].strip() else None,
                        loan_type=row.get('loan_type', '').strip() if row.get('loan_type') else None,
                        occupation=row.get('occupation', '').strip() if row.get('occupation') else None,
                        message=row.get('message', '').strip() if row.get('message') else None,
                        status='new',
                        additional_data=additional_data
                    )
                    
                    db.add(lead)
                    db.flush()  # Get the lead_id
                    
                    # Log activity
                    LeadService.log_activity(
                        db=db,
                        lead_id=lead.lead_id,
                        employee_id=created_by_employee_id,
                        activity_type='created',
                        description='Lead created via bulk import',
                        activity_data={'source': 'bulk_import', 'created_by': created_by_employee_id}
                    )
                    
                    success_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
                    error_count += 1
                    continue
            
            db.commit()
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Error processing CSV: {str(e)}")
        
        return {
            "success_count": success_count,
            "skipped_count": skipped_count,
            "error_count": error_count,
            "errors": errors
        }
    
    @staticmethod
    def get_lead_activities(db: Session, lead_id: int) -> List[LeadActivity]:
        """Get all activities for a lead"""
        return db.query(LeadActivity).filter(
            LeadActivity.lead_id == lead_id
        ).order_by(LeadActivity.created_at.desc()).all()
    
    @staticmethod
    def get_lead_timeline(db: Session, lead_id: int) -> List[Dict[str, Any]]:
        """Get formatted timeline for a lead"""
        activities = LeadService.get_lead_activities(db, lead_id)
        timeline = []
        
        for activity in activities:
            employee_name = "System"
            if activity.employee_id:
                employee = db.query(Employee).filter(Employee.employee_id == activity.employee_id).first()
                if employee and employee.user:
                    employee_name = employee.user.name
            
            timeline.append({
                'activity_id': activity.activity_id,
                'activity_type': activity.activity_type,
                'description': activity.description,
                'created_at': activity.created_at,  # Keep as datetime object for template
                'employee_name': employee_name,
                'activity_data': activity.activity_data
            })
        
        return timeline
    
    @staticmethod
    def get_all_leads(db: Session, filters: Dict[str, Any] = None) -> List[Lead]:
        """Get all leads with optional filtering"""
        query = db.query(Lead)
        
        if filters:
            if filters.get('status'):
                query = query.filter(Lead.status == filters['status'])
            if filters.get('source'):
                query = query.filter(Lead.source == filters['source'])
            if filters.get('employee_id'):
                # Filter by assigned employee
                query = query.join(LeadAssignment).filter(LeadAssignment.employee_id == filters['employee_id'])
        
        return query.order_by(Lead.created_at.desc()).all()
    
    @staticmethod
    def migrate_existing_leads(db: Session) -> Dict[str, int]:
        """Migrate existing website and social media leads to unified system"""
        migrated = {'website': 0, 'social': 0}
        
        # Migrate website leads
        website_leads = db.query(WebsiteLead).all()
        for old_lead in website_leads:
            # Check if already migrated
            existing = db.query(Lead).filter(
                Lead.additional_data.contains({'migrated_from': 'website_leads', 'original_id': old_lead.lead_id})
            ).first()
            
            if not existing:
                lead = Lead(
                    source='website',
                    name=old_lead.name,
                    contact=old_lead.contact,
                    email=old_lead.email,
                    message=old_lead.message,
                    status='new',
                    additional_data={
                        'migrated_from': 'website_leads',
                        'original_id': old_lead.lead_id
                    }
                )
                db.add(lead)
                migrated['website'] += 1
        
        # Migrate social media leads
        social_leads = db.query(SocialMediaLead).all()
        for old_lead in social_leads:
            # Check if already migrated
            existing = db.query(Lead).filter(
                Lead.additional_data.contains({'migrated_from': 'social_leads', 'original_id': old_lead.lead_id})
            ).first()
            
            if not existing:
                lead = Lead(
                    source='social',
                    name=old_lead.name,
                    contact=old_lead.contact,
                    city=old_lead.city,
                    loan_amount=old_lead.loan_amount,
                    platform_name=old_lead.platform_name,
                    any_ongoing_loan=old_lead.any_ongoing_loan,
                    status='new',
                    additional_data={
                        'migrated_from': 'social_leads',
                        'original_id': old_lead.lead_id
                    }
                )
                db.add(lead)
                migrated['social'] += 1
        
        db.commit()
        return migrated
    
    @staticmethod
    def update_pd_loan_amount(db: Session, assignment_id: int, amount: float, employee_id: int) -> bool:
        """Update PD loan amount"""
        assignment = db.query(LeadAssignment).filter(LeadAssignment.assignment_id == assignment_id).first()
        if not assignment:
            return False
        
        assignment.pd_loan_amount = amount
        assignment.last_updated = datetime.now()
        db.commit()
        
        # Log activity
        LeadService.log_activity(
            db=db,
            lead_id=assignment.lead_id,
            employee_id=employee_id,
            activity_type='pd_amount_updated',
            description=f'PD loan amount updated to ₹{amount:,.0f}',
            activity_data={'pd_amount': amount}
        )
        
        return True
    
    @staticmethod
    def update_approved_loan_amount(db: Session, assignment_id: int, amount: float, employee_id: int) -> bool:
        """Update approved loan amount"""
        assignment = db.query(LeadAssignment).filter(LeadAssignment.assignment_id == assignment_id).first()
        if not assignment:
            return False
        
        assignment.approved_loan_amount = amount
        assignment.last_updated = datetime.now()
        db.commit()
        
        # Log activity
        LeadService.log_activity(
            db=db,
            lead_id=assignment.lead_id,
            employee_id=employee_id,
            activity_type='approved_amount_updated',
            description=f'Approved loan amount updated to ₹{amount:,.0f}',
            activity_data={'approved_amount': amount}
        )
        
        return True
    
    @staticmethod
    def create_disbursement(db: Session, assignment_id: int, amount: float, disbursement_date: datetime,
                           disbursement_type: str, tranche_number: int, notes: str, employee_id: int) -> Disbursement:
        """Create a disbursement record"""
        disbursement = Disbursement(
            assignment_id=assignment_id,
            amount=amount,
            disbursement_date=disbursement_date,
            disbursement_type=disbursement_type,
            tranche_number=tranche_number,
            notes=notes,
            processed_by=employee_id
        )
        db.add(disbursement)
        
        # Update assignment status if this is a full disbursement
        assignment = db.query(LeadAssignment).filter(LeadAssignment.assignment_id == assignment_id).first()
        if assignment:
            total_disbursed = LeadService.get_total_disbursed_amount(db, assignment_id)
            if total_disbursed >= (assignment.approved_loan_amount or 0):
                assignment.status = 'disbursed'
                assignment.last_updated = datetime.now()
                
                # Update lead status
                lead = db.query(Lead).filter(Lead.lead_id == assignment.lead_id).first()
                if lead:
                    lead.status = 'disbursed'
        
        db.commit()
        db.refresh(disbursement)
        
        # Log activity
        LeadService.log_activity(
            db=db,
            lead_id=assignment.lead_id if assignment else None,
            employee_id=employee_id,
            activity_type='disbursement_created',
            description=f'Disbursement of ₹{amount:,.0f} created',
            activity_data={
                'amount': amount,
                'type': disbursement_type,
                'tranche': tranche_number,
                'notes': notes
            }
        )
        
        return disbursement
    
    @staticmethod
    def get_disbursements_for_assignment(db: Session, assignment_id: int) -> List[Disbursement]:
        """Get all disbursements for an assignment"""
        return db.query(Disbursement).filter(
            Disbursement.assignment_id == assignment_id
        ).order_by(Disbursement.disbursement_date.desc()).all()
    
    @staticmethod
    def get_total_disbursed_amount(db: Session, assignment_id: int) -> float:
        """Get total disbursed amount for an assignment"""
        result = db.query(func.sum(Disbursement.amount)).filter(
            Disbursement.assignment_id == assignment_id
        ).scalar()
        return result or 0.0
    
    @staticmethod
    def close_lead(db: Session, lead_id: int, close_type: str, close_reason: str, employee_id: int) -> bool:
        """Close a lead with two options: success or not doable"""
        from src.shared.crm_models import CloseLead
        
        print(f"DEBUG: LeadService.close_lead called with lead_id={lead_id}, close_type={close_type}")
        
        # Get the lead and assignment
        lead = db.query(Lead).filter(Lead.lead_id == lead_id).first()
        if not lead:
            print(f"DEBUG: Lead {lead_id} not found")
            return False
        
        print(f"DEBUG: Found lead: {lead.name}")
        
        assignment = db.query(LeadAssignment).filter(LeadAssignment.lead_id == lead_id).first()
        if assignment:
            print(f"DEBUG: Found assignment: {assignment.assignment_id}")
        else:
            print(f"DEBUG: No assignment found for lead {lead_id}")
        
        # Determine close message based on type
        close_message = "Closed - Success" if close_type == 'success' else "Closed - Not Doable"
        print(f"DEBUG: Close message: {close_message}")
        
        try:
            # Create close lead record
            close_lead = CloseLead(
                lead_id=lead_id,
                name=lead.name,
                contact=lead.contact,
                amount=assignment.approved_loan_amount if assignment else lead.loan_amount,
                close_message=close_message,
                close_reason=close_reason,
                closed_by=employee_id
            )
            print(f"DEBUG: Created CloseLead object: {close_lead}")
            db.add(close_lead)
            
            # Update lead status and state
            lead.status = 'closed'
            lead.state = 'closed'
            lead.updated_at = datetime.now()
            print(f"DEBUG: Updated lead status to closed")
            
            # Update assignment status if exists
            if assignment:
                assignment.status = 'closed'
                assignment.last_updated = datetime.now()
                print(f"DEBUG: Updated assignment status to closed")
            
            db.commit()
            print(f"DEBUG: Database committed successfully")
            
            # Log activity
            LeadService.log_activity(
                db=db,
                lead_id=lead_id,
                employee_id=employee_id,
                activity_type='lead_closed',
                description=f'Lead closed: {close_message}',
                activity_data={
                    'close_type': close_type,
                    'close_message': close_message,
                    'close_reason': close_reason
                }
            )
            print(f"DEBUG: Activity logged successfully")
            
            return True
        except Exception as e:
            print(f"DEBUG: Error in close_lead: {e}")
            import traceback
            traceback.print_exc()
            db.rollback()
            raise
    
    @staticmethod
    def update_lead_details(db: Session, lead_id: int, **kwargs) -> bool:
        """Update lead details with validation"""
        lead = db.query(Lead).filter(Lead.lead_id == lead_id).first()
        if not lead:
            return False
        
        # Initialize additional_data if it doesn't exist
        if not lead.additional_data:
            lead.additional_data = {}
        
        # Update allowed fields
        allowed_fields = ['name', 'contact', 'email', 'city', 'loan_amount', 'loan_type', 
                         'occupation', 'any_ongoing_loan', 'message', 'other_details', 'priority']
        
        # Fields to store in additional_data
        additional_fields = ['monthly_income', 'credit_score', 'employment_type', 
                           'preferred_contact_time', 'source_details']
        
        # Create a new additional_data dictionary
        new_additional_data = lead.additional_data.copy() if lead.additional_data else {}
        
        for field, value in kwargs.items():
            if field in allowed_fields and hasattr(lead, field):
                setattr(lead, field, value)
            elif field in additional_fields:
                # Store in additional_data
                new_additional_data[field] = value
            elif field == 'occupation_other' and value:
                # Handle custom occupation
                lead.occupation = value
        
        # Assign the new additional_data
        lead.additional_data = new_additional_data
        
        lead.updated_at = datetime.now()
        db.commit()
        
        return True
    
    @staticmethod
    def get_close_leads(db: Session, limit: int = 50) -> List[Dict[str, Any]]:
        """Get closed leads for review"""
        from src.shared.crm_models import CloseLead
        
        close_leads = db.query(CloseLead).join(Employee).order_by(
            CloseLead.closed_at.desc()
        ).limit(limit).all()
        
        return [
            {
                'close_id': cl.close_id,
                'lead_id': cl.lead_id,
                'name': cl.name,
                'contact': cl.contact,
                'amount': cl.amount,
                'close_message': cl.close_message,
                'close_reason': cl.close_reason,
                'closed_by': cl.employee.user.name,
                'closed_at': cl.closed_at.strftime('%d/%m/%Y %H:%M')
            }
            for cl in close_leads
        ]
    
    @staticmethod
    def get_workflow_progress(lead: Lead, assignment: LeadAssignment = None) -> List[Dict[str, Any]]:
        """Get workflow progress for visualization based on actual database structure"""
        
        # Get current status from assignment if available, otherwise from lead
        current_status = assignment.status if assignment else lead.status
        current_state = lead.state if lead else 'open'
        
        # Define the actual workflow stages based on database analysis
        workflow_stages = [
            {'status': 'new', 'label': 'New Lead', 'icon': 'bi-circle', 'order': 1},
            {'status': 'assigned', 'label': 'Assigned', 'icon': 'bi-person-check', 'order': 2},
            {'status': 'qualified', 'label': 'Qualified', 'icon': 'bi-check-circle', 'order': 3},
            {'status': 'pd', 'label': 'PD (Personal Discussion)', 'icon': 'bi-chat-dots', 'order': 4},
            {'status': 'documentation', 'label': 'Documentation', 'icon': 'bi-file-earmark-text', 'order': 5},
            {'status': 'login', 'label': 'Login', 'icon': 'bi-box-arrow-in-right', 'order': 6},
            {'status': 'underwriter', 'label': 'Underwriter', 'icon': 'bi-shield-check', 'order': 7},
            {'status': 'approved', 'label': 'Approved', 'icon': 'bi-check-circle-fill', 'order': 8},
            {'status': 'rejected', 'label': 'Rejected', 'icon': 'bi-x-circle-fill', 'order': 8},
            {'status': 'disbursed', 'label': 'Disbursed', 'icon': 'bi-cash-coin', 'order': 9},
            {'status': 'closed', 'label': 'Closed', 'icon': 'bi-archive', 'order': 10}
        ]
        
        progress = []
        
        # Handle closed leads differently
        if current_state == 'closed' or current_status == 'closed':
            # For closed leads, show a simplified path
            essential_stages = ['new', 'assigned', 'qualified']
            
            # Determine close reason and appropriate stages to show
            close_reason = "Not Doable"
            if assignment and assignment.close_type:
                if assignment.close_type == 'approved':
                    close_reason = "Success"
                    # For successful closures, show more stages as completed
                    essential_stages = ['new', 'assigned', 'qualified', 'pd', 'documentation', 'login', 'underwriter', 'approved']
                elif assignment.close_type == 'rejected':
                    close_reason = "Rejected"
                    # For rejected closures, show stages up to underwriter
                    essential_stages = ['new', 'assigned', 'qualified', 'pd', 'documentation', 'login', 'underwriter', 'rejected']
                else:
                    close_reason = "Not Doable"
            
            for stage in workflow_stages:
                status = stage['status']
                
                if status == 'closed':
                    # Show closed as completed (green) since it's the final state
                    progress.append({
                        **stage,
                        'label': f'Closed - {close_reason}',
                        'status_class': 'completed',
                        'completed': True
                    })
                elif status in essential_stages:
                    # Show essential stages as completed
                    progress.append({
                        **stage,
                        'status_class': 'completed',
                        'completed': True
                    })
                # Skip other stages for closed leads
        
        # Handle active leads
        else:
            # Determine which stages to show based on current status
            status_order = ['new', 'assigned', 'qualified', 'pd', 'documentation', 'login', 'underwriter', 'approved', 'rejected', 'disbursed']
            
            for stage in workflow_stages:
                status = stage['status']
                
                if status == current_status:
                    # Current stage
                    progress.append({
                        **stage,
                        'status_class': 'current',
                        'completed': False
                    })
                elif status == 'closed':
                    # Closed stage is always pending for active leads
                    progress.append({
                        **stage,
                        'status_class': 'pending',
                        'completed': False
                    })
                else:
                    # Check if this stage should be completed
                    if status in status_order and current_status in status_order:
                        stage_index = status_order.index(status)
                        current_index = status_order.index(current_status)
                        is_completed = stage_index < current_index
                    else:
                        is_completed = False
                    
                    # Special handling for approved/rejected branches
                    if status in ['approved', 'rejected'] and current_status in ['approved', 'rejected', 'disbursed']:
                        if status == current_status:
                            is_completed = True
                        elif status == 'approved' and current_status == 'disbursed':
                            is_completed = True
                        else:
                            is_completed = False
                    
                    progress.append({
                        **stage,
                        'status_class': 'completed' if is_completed else 'pending',
                        'completed': is_completed
                    })
        
        return progress
